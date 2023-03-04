import click
import os
import time
import httpx
import asyncio
from itertools import product

start_time = time.time()
script_path = os.path.dirname(os.path.abspath(__file__))
url_list_results = list()

BUCKET_URLS = [
    'https://storage.yandexcloud.net/{bucketname}',             # yandex
    'https://{bucketname}.hb.bizmrg.com',                       # vk_s3
    'https://{bucketname}.ib.bizmrg.com',                       # vk_s3
    'https://storage.cloud.croc.ru/{bucketname}',               # croc
    'https://{bucketname}.selcdn.ru',                           # selectel_s3
]

NAMESPACES_URLS = [
    'https://{namespace}.s3mts.ru/{bucketname}',                # mts_s3
    'https://{namespace}.s3pd01.sbercloud.ru/{bucketname}',     # sber_s3
    'https://{namespace}.s3pd02.sbercloud.ru/{bucketname}',     # sber_s3
    'https://{namespace}.s3pd11.sbercloud.ru/{bucketname}',     # sber_s3
    'https://{namespace}.s3pd12.sbercloud.ru/{bucketname}',     # sber_s3
    'https://{namespace}.s3pdgeob.sbercloud.ru/{bucketname}',   # sber_s3
]

# Urls where we expect to see the company domain name to be in somehow
# e.g. `mycompany.slack.com`, `dev-mycompany-internal.gitlab.yandexcloud.net`
SAAS_URLS = [
    'https://{name}.gitlab.yandexcloud.net',                    # yandex gitlab
    'https://{name}.website.yandexcloud.net',                   # yandex website
    'https://{name}.slack.com',                                 # slack
    'https://{name}.atlassian.net/login.jsp',                   # atlassian
    'https://{name}.my.salesforce.com',                         # salesforce
    # 'https://name.zendesk.com'                                # zendesk
]


def read_payload_file(file_path: str) -> list[str]:
    with open(file_path) as file_obj:
        return [line.strip() for line in file_obj.readlines() if line]


def uniq(func):
    def inner(*args, **kwargs):
        return list(set(func(*args, **kwargs)))
    return inner


@click.command()
@click.option('--name', '-n', help='Enter company\'s name', default='')
@click.option('--generate', help='Let cloudrecon generate all for you', type=bool, is_flag=True, default=False)
@click.option('--namespaces', type=click.Path(exists=True), help='File with generated namespaces',
              default=os.path.join(script_path, 'namespaces.txt'))
@click.option('--buckets', type=click.Path(exists=True), help='File with generated bucket names',
              default=os.path.join(script_path, 'bucketnames.txt'))
@click.option('--rps', '-rps', help='Enter number of requests per second to init', type=int, default=100)
def cloudrec(name, generate, namespaces, buckets, rps):

    namespaces_data = read_payload_file(namespaces)
    bucketnames_data = read_payload_file(buckets)

    if generate:
        mutations = generate_mutations(name, namespaces_data)
        enum_urls = generate_enum_payload(saas_payload=mutations,
                                          buckets_payload=mutations,
                                          s3_buckets_payload=(mutations, bucketnames_data))
    else:
        enum_urls = generate_enum_payload(saas_payload=[name],
                                          buckets_payload=bucketnames_data,
                                          s3_buckets_payload=(namespaces_data, bucketnames_data))

    timeout = 200 * round(100 / rps, 2)
    print_stats(name, namespaces, buckets, timeout, rps, enum_urls)
    asyncio.run(brute(enum_urls, rps, timeout))

    print(f"Time elapsed: {str(time.time() - start_time)}")
    print(f'Fund {len(url_list_results)} results')


def print_stats(name, namespaces, buckets, timeout, rps, enum_urls):
    print(f"[*] Enumerating for name: {name}")
    print(f"[*] Buckets filename: {buckets}")
    print(f"[*] Namespaces filename: {namespaces}")
    print(f"[*] Timeout: {timeout}")
    print(f"[*] Requests per second: {rps}")
    print(f"[*] Total list length: {len(enum_urls)}")


async def get(client, url):
    failed_http_codes = [404, 434, 400]

    try:
        resp = await client.get(url)
        if resp.status_code not in failed_http_codes:
            url_list_results.append({'url': url, 'code': resp.status_code})
            print(f"[+] Found - {url} : {str(resp.status_code)}")
    except Exception:
        pass


@uniq
def generate_mutations(company_name: str, mutation_payload: list[str]) -> list[str]:
    mutations = [company_name]

    for mutation in mutation_payload:
        mutations.append(f"{mutation}-{company_name}")
        mutations.append(f"{company_name}-{mutation}")

    return mutations


def generate_enum_payload(saas_payload: list[str], buckets_payload: list[str], s3_buckets_payload: tuple[list[str], list[str]]) -> list[str]:
    """
    @param saas_payload: a list of strings for SAAS_URLS
    @param buckets_payload: a list of strings for BUCKET_URLS
    @param s3_buckets_payload: a list of strings for 'namespace' in NAMESPACES_URLS
    @return:
    """
    urls = enum_saas(saas_payload) + enum_buckets(buckets_payload) + \
        enum_buckets_with_namespaces(s3_buckets_payload[0], s3_buckets_payload[1])
    urls.sort()
    return urls


@uniq
def fill_template(template_urls: list[str], mutations: list[str], field_name: str) -> list[str]:
    """ Fills template urls.
    @param template_urls: a list of urls, e.g.
        [ 'https://{bucketname}.hb.bizmrg.com', ... ]
    @param mutations: a list of strings to be substituted in the urls
    @param field_name: a string to be replaced, e.g. `bucketname`
    @return: list of urls with ...
    """
    urls = []
    for tmp_url in template_urls:
        urls += [tmp_url.format(**{field_name: mutation}) for mutation in mutations]
    return urls


def enum_saas(mutations: list[str]) -> list[str]:
    return fill_template(template_urls=SAAS_URLS, mutations=mutations, field_name='name')


def enum_buckets(mutations: list[str]) -> list[str]:
    return fill_template(template_urls=BUCKET_URLS, mutations=mutations, field_name='bucketname')


@uniq
def enum_buckets_with_namespaces(mutations: list[str], bucketnames: list[str]) -> list[str]:
    """
    MTS Cloud S3: http(s)://{namespace}.s3mts.ru/{bucket}/file/
    SberCloud S3: https://{namespace}.s3pd02.sbercloud.ru/{bucket}
    """
    generated_urls = []
    for url in NAMESPACES_URLS:
        for pair in [(ns, bucket) for ns, bucket in product(mutations, bucketnames)]:
            generated_urls.append(url.format(namespace=pair[0], bucketname=pair[1]))
    return generated_urls


async def brute(enum_urls, rps, timeout):
    limits = httpx.Limits(max_connections=rps)
    tasks = []

    async with httpx.AsyncClient(verify=False, limits=limits, timeout=timeout, follow_redirects=True) as client:
        for url in enum_urls:
            tasks.append(asyncio.ensure_future(get(client, url)))

        res = await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == '__main__':
    cloudrec()
