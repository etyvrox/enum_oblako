import click
import os
import time
import httpx
import asyncio
from itertools import product

start_time = time.time()
script_path = os.path.dirname(os.path.abspath(__file__))
conf = {}
url_list = []
url_list_results = list()

# Urls with both bucket names only
BUCKET_URLS = [
    'https://storage.yandexcloud.net/{bucketname}',             # yandex
    'https://{bucketname}.hb.bizmrg.com',                       # vk_s3
    'https://{bucketname}.ib.bizmrg.com',                       # vk_s3
    'https://storage.cloud.croc.ru/{bucketname}',               # croc
    'https://{bucketname}.selcdn.ru',                           # selectel_s3
]

# Urls with both bucket name and namespace mutable
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


def read_payload_file(file_path):
    """
    Reads a file and returns a list of strings
    """
    with open(file_path) as file_obj:
        return [line.strip() for line in file_obj.readlines()]


@click.command()
@click.option('--name', '-n', help='Enter company\'s name', default='')
@click.option('--generate', help='Let cloudrecon generate all for you', type=bool, is_flag=True, default=False)
@click.option('--namespaces', type=click.Path(exists=True), help='File with generated namespaces',
              default=os.path.join(script_path, 'namespaces.txt'))
@click.option('--buckets', type=click.Path(exists=True), help='File with generated bucket names',
              default=os.path.join(script_path, 'bucketnames.txt'))
@click.option('--rps', '-rps', help='Enter number of requests per second to init', type=int, default=100)
def cloudrec(name, generate, namespaces, buckets, rps):
    global conf

    conf = {
        'name': name,
        'namespaces': namespaces,
        'buckets': buckets,
        'rps': rps
    }

    conf['timeout'] = 200 * round(100 / conf['rps'], 2)

    if generate:
        gen(name)
    else:
        enum(name, namespaces, buckets)

    prepare_url_list()

    print_stats()
    asyncio.run(brute())

    print(f"Time elapsed: {str(time.time() - start_time)}")
    print(f'Fund {len(url_list_results)} results')


def print_stats():
    print(f"[*] Enumerating for name: {conf['name']}")
    print(f"[*] Buckets filename: {conf['buckets']}")
    print(f"[*] Namespaces filename: {conf['namespaces']}")
    print(f"[*] Timeout: {conf['timeout']}")
    print(f"[*] Requests per second: {conf['rps']}")
    print(f"[*] Total list length: {len(url_list)}")


async def get(client, url):
    failed_http_codes = [404, 434, 400]

    try:
        resp = await client.get(url)
        if resp.status_code not in failed_http_codes:
            url_list_results.append({'url': url, 'code': resp.status_code})
            print(f"[+] Found - {url} : {str(resp.status_code)}")
    except Exception:
        pass


def add(url):
    global url_list
    url_list.append(url)


def prepare_url_list():
    global url_list
    url_list.sort()
    url_list = list(set(url_list))


def generate_mutations(company_name):
    mutations = [company_name]

    for mutation in read_payload_file(conf['namespaces']):
        mutations.append(f"{mutation}-{company_name}")
        mutations.append(f"{company_name}-{mutation}")
    return mutations


def gen(name):
    mutations = generate_mutations(name)

    enum_saas(mutations)
    enum_buckets(mutations)
    enum_buckets_with_namespaces(mutations, conf['buckets'])


def enum(name, namespaces, buckets):
    temp = [name]
    enum_saas(temp)
    enum_s3(temp, namespaces, buckets)


def enum_s3(name, namespaces, buckets):
    temp_list = []

    for namespace in read_payload_file(namespaces):
        for url in NAMESPACES_URLS:
            temp_list.append(url.replace('namespace', namespace))

    bucketnames = read_payload_file(buckets) + name

    for bucket in bucketnames:
        for url in BUCKET_URLS + temp_list:
            add(url.replace('bucketname', bucket))


def enum_saas(mutations):
    for url in SAAS_URLS:
        for generated_saas_url in [url.format(name=mutation) for mutation in mutations]:
            add(generated_saas_url)


def enum_buckets(mutations):
    for url in BUCKET_URLS:
        for generated_bucket_url in [url.format(bucketname=mutation) for mutation in mutations]:
            add(generated_bucket_url)


def enum_buckets_with_namespaces(mutations, buckets_file_path):
    """
    MTS Cloud S3: http(s)://{namespace}.s3mts.ru/{bucket}/file/
    SberCloud S3: https://{namespace}.s3pd02.sbercloud.ru/{bucket}
    """
    with open(buckets_file_path) as buckets_f:
        bucketnames = [line.strip() for line in buckets_f.readlines()]

    for url in NAMESPACES_URLS:
        for pair in [(ns, bucket) for ns, bucket in product(mutations, bucketnames)]:
            add(url.format(namespace=pair[0], bucketname=pair[1]))


async def brute():
    limits = httpx.Limits(max_connections=conf['rps'])
    tasks = []

    async with httpx.AsyncClient(verify=False, limits=limits, timeout=conf['timeout'], follow_redirects=True) as client:
        for url in url_list:
            tasks.append(asyncio.ensure_future(get(client, url)))

        res = await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == '__main__':
    cloudrec()
