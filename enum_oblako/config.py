GL = [
    "https://{name}.slack.com",  # slack
    "https://{name}.atlassian.net/login.jsp",  # atlassian
    "https://{name}.my.salesforce.com",
]

EU_BUCKET_URLS = [
    "https://s3.nl-ams.scw.cloud/{bucketname}",
    "https://s3.fr-par.scw.cloud/{bucketname}",
    "https://s3.pl-waw.scw.cloud/{bucketname}",
    "https://sos-ch-dk-2.exo.io/{bucketname}",
    "https://sos-ch-gva-2.exo.io/{bucketname}",
    "https://sos-bg-sof-1.exe.io/{bucketname}",
    "https://sos-de-muc-1.exo.io/{bucketname}",
    "https://sos-at-vie-1.exo.io/{bucketname}",
    "https://sos-de-fra-1.exo.io/{bucketname}",
    "https://{bucketname}.s3.gra.io.cloud.ovh.net",
    "https://{bucketname}.s3.sbg.io.cloud.ovh.net",
    "https://{bucketname}.s3.bhs.io.cloud.ovh.net",
    "https://{bucketname}.s3.rbx.io.cloud.ovh.net",
    "https://{bucketname}.s3.gra.perf.cloud.ovh.net",
    "https://{bucketname}.s3.sbg.perf.cloud.ovh.net",
    "https://{bucketname}.s3.bhs.perf.cloud.ovh.net",
    "https://{bucketname}.s3.sbg.cloud.ovh.net",
    "https://{bucketname}.s3.uk.cloud.ovh.net",
    "https://{bucketname}.s3.de.cloud.ovh.net",
    "https://{bucketname}.s3.waw.cloud.ovh.net",
    "https://{bucketname}.s3.bhs.cloud.ovh.net",
    "https://{bucketname}.s3.gra.cloud.ovh.net",
    "https://s3-eu-central-1.ionoscloud.com/{bucketname}",
    "https://s3-eu-central-2.ionoscloud.com/{bucketname}",
    "https://s3-eu-south-2.ionoscloud.com/{bucketname}",
    "https://us-southeast-1.linodeobjects.com/{bucketname}",
    "https://eu-central-1.linodeobjects.com/{bucketname}",
    "https://us-east-1.linodeobjects.com/{bucketname}",
    "https://ap-south-1.linodeobjects.com/{bucketname}",
    "https://ams1.vultrobjects.com/{bucketname}",
    "https://blr1.vultrobjects.com/{bucketname}",
    "https://ewr1.vultrobjects.com/{bucketname}",
    "https://sjc1.vultrobjects.com/{bucketname}",
    "https://sgp1.vultrobjects.com/{bucketname}",
    "https://nyc3.digitaloceanspaces.com/{bucketname}",
    "https://fra1.digitaloceanspaces.com/{bucketname}",
]

RU_BUCKET_URLS = [
    "https://storage.yandexcloud.net/{bucketname}",  # yandex
    "https://{bucketname}.hb.bizmrg.com",  # vk_s3
    "https://{bucketname}.ib.bizmrg.com",  # vk_s3
    "https://storage.cloud.croc.ru/{bucketname}",  # croc
    "https://{bucketname}.selcdn.ru",  # selectel_s3
]

RU_NAMESPACES_URLS = [
    "https://{namespace}.s3mts.ru/{bucketname}",  # mts_s3
    "https://{namespace}.s3pd01.sbercloud.ru/{bucketname}",  # sber_s3
    "https://{namespace}.s3pd02.sbercloud.ru/{bucketname}",  # sber_s3
    "https://{namespace}.s3pd11.sbercloud.ru/{bucketname}",  # sber_s3
    "https://{namespace}.s3pd12.sbercloud.ru/{bucketname}",  # sber_s3
    "https://{namespace}.s3pdgeob.sbercloud.ru/{bucketname}",  # sber_s3
]

# Urls where we expect to see the company domain name to be in somehow
# e.g. `mycompany.slack.com`, `dev-mycompany-internal.gitlab.yandexcloud.net`
RU_SAAS_URLS = [
    "https://{name}.gitlab.yandexcloud.net",  # yandex gitlab
    "https://{name}.website.yandexcloud.net",  # yandex website
]
