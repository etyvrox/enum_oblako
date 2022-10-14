import click
import os
import sys
import time
import httpx
import asyncio


start_time = time.time()
script_path = os.path.split(os.path.abspath(sys.argv[0]))[0]
conf = {}
url_list = []

bucket_urls = [
        'https://storage.yandexcloud.net/bucketname',        #yandex
        'https://bucketname.hb.bizmrg.com',                  #vk_s3
        'https://bucketname.ib.bizmrg.com',                  #vk_s3
        'https://storage.cloud.croc.ru/bucketname',          #croc
        'https://bucketname.selcdn.ru',                      #selectel_s3
]
namespaces_urls = [
        'https://namespace.s3mts.ru/bucketname',             #mts_s3
        'https://namespace.s3pd01.sbercloud.ru/bucketname',  #sber_s3
        'https://namespace.s3pd02.sbercloud.ru/bucketname',  #sber_s3
        'https://namespace.s3pd11.sbercloud.ru/bucketname',  #sber_s3
        'https://namespace.s3pd12.sbercloud.ru/bucketname',  #sber_s3
        'https://namespace.s3pdgeob.sbercloud.ru/bucketname',#sber_s3
]
saas_urls = [
            'https://name.gitlab.yandexcloud.net',    #yandex gitlab
            'https://name.website.yandexcloud.net',   #yandex website
            'https://name.slack.com',                 #slack
            'https://name.atlassian.net/login.jsp',   #atlassian
            'https://name.my.salesforce.com',         #salesforce
            #'https://name.zendesk.com'               #zendesk
]

@click.command()
@click.option('--name', '-n', help='Enter company\'s name', default='' )
@click.option('--generate', help='Let cloudrecon generate all for you', type=bool, is_flag=True, default=False)
@click.option('--namespaces', type=click.Path(exists=True), help='File with generated namespaces')
@click.option('--buckets', type=click.Path(exists=True), help='File with generated bucket names')
@click.option('--rps', '-rps', help = 'Enter number of requests per second to init', type=int, default=100)

def cloudrec(name, generate, namespaces, buckets, rps):
    global conf, start_time

    conf = {
            'name':name,
            'generate':generate,
            'namespaces':namespaces,
            'buckets':buckets,
            'rps':rps
            }
    conf['timeout'] = 200 * round(100/conf['rps'], 2)


    if (generate):
        gen(name)
        print_stats()
        asyncio.run(brute())
        print(f" Time elapsed {str(time.time() - start_time)}")
    else:
        enum(name,namespaces, buckets)
        print_stats()
        asyncio.run(brute())
        print ("{*} Time elapsed - %s" % str(time.time() - start_time))

def print_stats():
    print (f"[*] Enumerating for name {conf['name']}")
    print (f"[*] Buckets' filename {conf['buckets']}")
    print (f"[*] Namespaces' filename {conf['namespaces']}")
    print (f"[*] Timeout is {conf['timeout']}")
    print (f"[*] Requests per second is {conf['rps']}")
    print (f"[*] Total list length is {len(url_list)}")


async def get(client, url):
    failed_http_codes = [404, 434, 400]

    try:
        resp = await client.get(url)
        if ( resp.status_code not in failed_http_codes ):
            res = "[+] Found - " + url + " : " + str(resp.status_code)
            print (res)
    except Exception as e:
        pass


def add(url):
    global url_list
    url_list.append(url)


def gen(name):
    mutations = []
    conf['buckets'] = script_path + '/bucketnames.txt'
    conf['namespaces'] = script_path + '/namespaces.txt'

    bucketnames = [line.replace('\n','') for line in open(script_path + '/bucketnames.txt')]
    namespaces = [line.replace('\n','') for line in open(script_path + '/namespaces.txt')]
    
    mutations.append(name)

    for mutation in namespaces:
        mutations.append(f"{mutation}-{name}")
        mutations.append(f"{name}-{mutation}")
    
    enum_saas(mutations)    

    for url in bucket_urls:
        for mutation in mutations:
            add(url.replace('bucketname', mutation))

    for mutation in mutations:
        for url in namespaces_urls:
            for bucket in bucketnames:
                add((url.replace('namespace', mutation)).replace('bucketname', bucket))


def enum(name,namespaces, buckets):
    temp = []
    temp.append(name)
    enum_saas(temp)
    enum_s3(temp, namespaces, buckets)


def enum_s3(name, namespaces, buckets):
    global start_time, bucket_urls, namespaces_urls
    temp_list = []

    bucketnames = [bucket.replace('\n','') for bucket in open(buckets)]
    namespaces = [namespace.replace('\n','') for namespace in open(namespaces)]
    bucketnames += name

    for namespace in namespaces:
        for url in namespaces_urls:
            temp_list.append(url.replace('namespace', namespace))
    
    bucket_urls += temp_list

    for bucket in bucketnames:
        for url in bucket_urls:
            add(url.replace('bucketname', bucket))


def enum_saas(name):
    for mutation in name:
        for url in saas_urls:
            add(url.replace('name', mutation))

async def brute():
    global url_list, conf

    url_list.sort()
    limits = httpx.Limits(max_connections=conf['rps'])
    tasks = []

    async with httpx.AsyncClient(verify=False, limits=limits, timeout=conf['timeout'], follow_redirects=True) as client:
        for url in url_list:
            tasks.append(asyncio.ensure_future(get(client, url)))
        
        res = await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == '__main__':
    cloudrec()