# Changelog

All notable changes to this project can be found here.
The format of this changelog is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

#### 2026/07/15 [2.1.0](https://github.com/UACoreFacilitiesIT/UA-Generic-Rest-API/)

Updated ascyncio calls, added max workers with a timeout at 60s, updated unit tests

#### 2023/11/21 [2.0.6](https://github.com/UACoreFacilitiesIT/UA-Generic-Rest-API/)

Removed requirements.txt, setup.py, and twine as packaging tools. Now, it uses poetry.


#### 2020/1/20 [2.0.5](https://github.com/UACoreFacilitiesIT/UA-Generic-Rest-API/)

Updated setup.py dependencies to be more explicit and contain every dependency.

- Previously some dependencies were not listed, but were assumed to be installed through other packages.

#### 2020/02/17[2.0.4](https://github.com/UACoreFacilitiesIT/UA-Generic-Rest-API/)

Fixed issue where query builder might create a url of more than 2000 characters when building a query. It not will split the url into multiple pieces each of less than 2000 characters, and attempt to batch get them.

#### 2020/01/29[2.0.3](https://github.com/UACoreFacilitiesIT/UA-Generic-Rest-API/)

Bug fix that stopped queries which are substrings of queries from being added. Now, queries are added in sorted order, guaranteeing that substring queries are added before other ones.

#### 2020/01/16[2.0.2](https://github.com/UACoreFacilitiesIT/UA-Generic-Rest-API/)

Bug fix with querying multiple values under the same tag. Previously queries for that tag would be empty and now they actually contain all of the requested values.

#### 2019/12/05[2.0.1](https://github.com/UACoreFacilitiesIT/UA-Generic-Rest-API/)

Small changes to the _query_builder function, which now builds queries based on a set of given queries to avoid repeating the same query multiple times.

#### 2019/10/08[2.0.0](https://github.com/UACoreFacilitiesIT/UA-Generic-Rest-API/)

In this new release, the get function is not as specific as it used to be. Now you can pass in the keyword "total_pages" to get all pages, but the "next_page" concept has been removed.

#### 2019/10/03 [1.0.0](https://github.com/UACoreFacilitiesIT/UA-Generic-Rest-API/commit/1854437081a4e1769b7dc6dff588c2a68703a0cb)

This is the initial start point for a University of Arizona Generic Rest API.

- Moved repo from private repo to public.
