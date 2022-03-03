# Copyright 2022 Fengying
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
import re
import shutil
import sys
import tempfile
import time

from gitignore_parser import handle_negation, rule_from_pattern
from steamworks import STEAMWORKS
from steamworks.enums import ERemoteStoragePublishedFileVisibility, EResult, EWorkshopFileType
from steamworks.structs import CreateItemResult_t, SubmitItemUpdateResult_t

if __name__ != "__main__":
    exit()

if sys.argv[1] == "upload":
    test = False
elif sys.argv[1] == "build":
    test = True
else:
    exit("Command line parameter error.")

finished = False

mod_path = os.path.abspath(sys.argv[2])
os.chdir(mod_path)

if not os.path.exists("modinfo.lua") or not os.path.exists("modmain.lua"):
    exit("modinfo.lua or modmain.lua not found.")

with open("modinfo.lua", "r", encoding='utf-8') as modinfo_file:
    modinfo = modinfo_file.read()

    def re_getconfig(pattern1, pattern2):
        re_result = re.search(pattern1, modinfo)
        if re_result:
            re_result = re.search(pattern2, re_result[0])
            if re_result:
                return re_result[0]
        return None

    mod_version = re_getconfig('version[\s]*=[\s]*".*?"', '".*?"')

    if not mod_version:
        exit("Mod version not set in modinfo.lua")

    modinfoTags = [f"version:{mod_version[1:-1]}"]

    client_only_mod = re_getconfig('client_only_mod[\s]*=[\s]*(true|false)', "true|false")
    if client_only_mod == "true":
        modinfoTags.append("client_only_mod")

    all_clients_require_mod = re_getconfig('all_clients_require_mod[\s]*=[\s]*(true|false)',
                                           "true|false")
    if all_clients_require_mod == "true":
        modinfoTags.append("all_clients_require_mod")

    server_only_mod = re_getconfig('server_only_mod[\s]*=[\s]*(true|false)', "true|false")
    if server_only_mod == "true":
        modinfoTags.append("server_only_mod")

if not os.path.exists(".uploader-config.json"):
    exit("No uploader.json file")

with open(".uploader-config.json", "r", encoding='utf-8') as config_file:
    updateConfig = json.load(config_file)

exclude = []

if updateConfig["git_exclude"] and os.path.exists(".gitignore"):
    with open(".gitignore", encoding='utf-8') as gitignore:
        exclude.extend(gitignore.read().split("\n"))

exclude.extend(updateConfig["exclude"])

rules = [rule_from_pattern(pattern) for pattern in exclude]
if not any(r.negation for r in rules):
    filter = lambda file_path: any(r.match(file_path) for r in rules)
else:
    # We have negation rules. We can't use a simple "any" to evaluate them.
    # Later rules override earlier rules.
    filter = lambda file_path: handle_negation(file_path, rules)


def upload_ignore_filter(path, names):
    excluded_names = []

    for name in names:
        if filter(os.path.join(path, name)):
            excluded_names.append(name)

    return set(excluded_names)


if test:
    shutil.rmtree("./release", ignore_errors=True)
    shutil.copytree(".", "./release", ignore=upload_ignore_filter, dirs_exist_ok=True)
    exit()

with tempfile.TemporaryDirectory() as tmpdirname:
    os.chdir(os.path.dirname(__file__))
    steamworks = STEAMWORKS(".")
    steamworks.initialize()

    os.chdir(mod_path)
    shutil.copytree(".", tmpdirname, ignore=upload_ignore_filter, dirs_exist_ok=True)

    def updateCallback(result: SubmitItemUpdateResult_t):
        if result.result == EResult.OK.value:
            updateConfig["update_titles"] = False
            updateConfig["update_description"] = False
            updateConfig["update_previewFile"] = False
            updateConfig["update_visibility"] = False
            updateConfig["change_note"] = ""
            with open(".uploader-config.json", "w", encoding='utf-8') as config_file:
                json.dump(updateConfig, config_file, ensure_ascii=False, indent=4)
            global finished
            finished = True

    def DoUpdate(publishedFileId):
        print(f"Mod ID to be updated is {publishedFileId}")
        updateConfig["publishedFileId"] = publishedFileId
        updateHandler = steamworks.Workshop.StartItemUpdate(322330, publishedFileId)
        if updateConfig["update_titles"]:
            steamworks.Workshop.SetItemTitle(updateHandler, updateConfig["title"])
            print(f'New item title: {updateConfig["title"]}')
        if updateConfig["update_description"]:
            steamworks.Workshop.SetItemDescription(updateHandler, updateConfig["description"])
        if updateConfig["update_previewFile"]:
            steamworks.Workshop.SetItemPreview(updateHandler,
                                               os.path.abspath(updateConfig["previewFile"]))
            print(f'New item preview: {os.path.abspath(updateConfig["previewFile"])}')
        if updateConfig["update_visibility"]:
            steamworks.Workshop.SetItemVisibility(
                updateHandler, ERemoteStoragePublishedFileVisibility(updateConfig["visibility"]))
            print(
                f'Mod is now visibility to: {ERemoteStoragePublishedFileVisibility(updateConfig["visibility"]).name}'
            )

        steamworks.Workshop.SetItemTags(updateHandler, updateConfig["tags"] + modinfoTags)
        print(f'Item is tagged with {updateConfig["tags"]}')
        steamworks.Workshop.SetItemContent(updateHandler, tmpdirname)
        if input("Is this ok?[y/n]") != "y":
            exit()
        print("Starting to upload")
        steamworks.Workshop.SubmitItemUpdate(updateHandler, updateConfig["change_note"],
                                             updateCallback, True)

    def createCallback(result: CreateItemResult_t):
        if result.result == EResult.OK.value:
            DoUpdate(result.publishedFileId)
        print("Failed to create a new workshop item")

    if not updateConfig["publishedFileId"] or updateConfig["publishedFileId"] == 0:
        print("No publishId, trying to create a new workshop item")
        steamworks.Workshop.CreateItem(322330, EWorkshopFileType.COMMUNITY, createCallback, True)
    else:
        DoUpdate(updateConfig["publishedFileId"])

    while not finished:
        steamworks.run_callbacks()
        time.sleep(1)

    print("Mod uploading finished successfully")
    time.sleep(1)
