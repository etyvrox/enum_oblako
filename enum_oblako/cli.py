import asyncio
import os
import time
from itertools import product
from typing import Generator

import aiohttp
import click

from .config import EU_BUCKET_URLS, GL, RU_BUCKET_URLS, RU_NAMESPACES_URLS, RU_SAAS_URLS

start_time = time.time()
script_path = os.path.dirname(os.path.abspath(__file__))
url_list_results = list()

SAAS_URLS = GL
BUCKET_URLS = []
NAMESPACES_URLS = []


def read_payload_file(file_path: str) -> list[str]:
    with open(file_path) as file_obj:
        return (line.strip() for line in file_obj.readlines() if line)


def uniq(func):
    def inner(*args, **kwargs):
        return list(set(func(*args, **kwargs)))

    return inner


@click.command()
@click.option("--name", "-n", help="Enter company's name", default="")
@click.option(
    "--generate",
    help="Let cloudrecon generate all for you",
    type=bool,
    is_flag=True,
    default=False,
)
@click.option(
    "--namespaces",
    type=click.Path(exists=True),
    help="File with generated namespaces",
    default=os.path.join(script_path, "namespaces.txt"),
)
@click.option(
    "--buckets",
    type=click.Path(exists=True),
    help="File with generated bucket names",
    default=os.path.join(script_path, "bucketnames.txt"),
)
@click.option(
    "--rps",
    "-rps",
    help="Enter number of requests per second to init",
    type=int,
    default=100,
)
@click.option(
    "--region",
    "-r",
    help="Enter region in which to search (all, ru, eu, apac, mea) Default: all",
    type=str,
    default="all",
)
def cloudrec(name, generate, namespaces, buckets, rps, region):
    namespaces_data = read_payload_file(namespaces)
    bucketnames_data = read_payload_file(buckets)
    global BUCKET_URLS, NAMESPACES_URLS, SAAS_URLS

    if region == "eu":
        BUCKET_URLS += EU_BUCKET_URLS
    elif region == "ru":
        BUCKET_URLS += RU_BUCKET_URLS
        NAMESPACES_URLS += RU_NAMESPACES_URLS
        SAAS_URLS += RU_SAAS_URLS
    elif region == "all":
        BUCKET_URLS += EU_BUCKET_URLS + RU_BUCKET_URLS
        NAMESPACES_URLS += RU_NAMESPACES_URLS
        SAAS_URLS += RU_SAAS_URLS

    if generate:
        mutations = generate_mutations(name, namespaces_data)
        gen = generate_enum_payload_chunk(
            saas_payload=mutations,
            buckets_payload=mutations,
            s3_buckets_payload=(mutations, bucketnames_data),
        )
    else:
        gen = generate_enum_payload_chunk(
            saas_payload=[name],
            buckets_payload=bucketnames_data,
            s3_buckets_payload=(namespaces_data, bucketnames_data),
        )

    print_stats(name, namespaces, buckets, rps)

    asyncio.run(brute(gen, rps))

    print(f"Time elapsed: {str(time.time() - start_time)}")
    print(f"Found {len(url_list_results)} results")


def print_stats(name, namespaces, buckets, rps):
    print(f"[*] Enumerating for name: {name}")
    print(f"[*] Buckets filename: {buckets}")
    print(f"[*] Namespaces filename: {namespaces}")
    print(f"[*] Requests per second: {rps}")


async def get(client, queue):
    failed_http_codes = [404, 434, 400, 429]
    while True:
        url = await queue.get()
        # print (' ' * 80, end='\r')
        # print (f"Trying {url}", end="\r")

        try:
            resp = await client.get(url, allow_redirects=True)
            if resp.status not in failed_http_codes:
                url_list_results.append({"url": url, "code": resp.status})
                print(f"[+] Found - {url} : {str(resp.status)}")
        except Exception:
            pass
        finally:
            queue.task_done()


@uniq
def generate_mutations(company_name: str, mutation_payload: list[str]) -> list[str]:
    mutations = [company_name]

    for mutation in mutation_payload:
        mutations.append(f"{mutation}-{company_name}")
        mutations.append(f"{company_name}-{mutation}")

    return mutations


def generate_enum_payload_chunk(
    saas_payload: list[str],
    buckets_payload: list[str],
    s3_buckets_payload: tuple[list[str], list[str]],
) -> Generator[str, None, None]:
    """
    @param saas_payload: a list of strings for SAAS_URLS
    @param buckets_payload: a list of strings for BUCKET_URLS
    @param s3_buckets_payload: a list of strings for 'namespace' in NAMESPACES_URLS
    @yield: `str` mutated url
    """

    _enum_saas = enum_saas(saas_payload)
    for res in _enum_saas:
        yield res

    _enum_buckets = enum_buckets(buckets_payload)
    for res in _enum_buckets:
        yield res

    _enum_buckets_with_namespaces = enum_buckets_with_namespaces(
        s3_buckets_payload[0], s3_buckets_payload[1]
    )
    for res in _enum_buckets_with_namespaces:
        yield res


def fill_template(
    template_urls: list[str], mutations: list[str], field_name: str
) -> Generator[str, None, None]:
    """Fills template urls.
    @param template_urls: a list of urls, e.g.
        [ 'https://{bucketname}.hb.bizmrg.com', ... ]
    @param mutations: a list of strings to be substituted in the urls
    @param field_name: a string to be replaced, e.g. `bucketname`
    @yield: list of urls with ...
    """

    for tmp_url in template_urls:
        for mutation in mutations:
            yield tmp_url.format(**{field_name: mutation})


def enum_saas(mutations: list[str]) -> list[str]:
    return fill_template(
        template_urls=SAAS_URLS, mutations=mutations, field_name="name"
    )


def enum_buckets(mutations: list[str]) -> list[str]:
    return fill_template(
        template_urls=BUCKET_URLS, mutations=mutations, field_name="bucketname"
    )


def enum_buckets_with_namespaces(
    mutations: list[str], bucketnames: list[str]
) -> list[str]:
    """
    MTS Cloud S3: http(s)://{namespace}.s3mts.ru/{bucket}/file/
    SberCloud S3: https://{namespace}.s3pd02.sbercloud.ru/{bucket}
    """

    for url in NAMESPACES_URLS:
        for pair in [(ns, bucket) for ns, bucket in product(mutations, bucketnames)]:
            yield url.format(namespace=pair[0], bucketname=pair[1])


async def brute(gen, rps):
    tasks = []
    queue = asyncio.Queue(maxsize=1000)
    connector = aiohttp.TCPConnector(limit=rps, ssl=False)
    async with aiohttp.ClientSession(connector=connector) as sess:
        for i in range(100):
            task = asyncio.create_task(get(sess, queue))
            tasks.append(task)

        for url in gen:
            await queue.put(url)

        await queue.join()

        for task in tasks:
            task.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)

        await sess.close()


if __name__ == "__main__":
    cloudrec()
