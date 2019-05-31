#!/usr/bin/python3


import os
from html.parser import HTMLParser


current_path = os.path.dirname(os.path.realpath(__file__))
client_dict = {}
errors = []


def list_files(root_dir):
    file_list = []

    for path, subdirs, files in os.walk(root_dir):
        for name in files:
            file_path = os.path.join(path, name)

            if file_path.endswith('.htm') or file_path.endswith('.html'):
                file_list.append(file_path)

    return file_list


def read_file(file_path):
    content = ""

    # Read with default encoding while you can
    try:
        with open(file_path, 'rb') as fp:
            while True:
                content += fp.read(10).decode()

    except Exception as e:
        pass

    try:
        encode = content.split('charset=')[1].split('"')[0]
    except:
        try:
            encode = content.split('charset=')[1].split(';')[0]
        except:
            encode = 'utf-8windows-1250'

    f = open(file_path, 'r', encoding=encode)
    content = f.read()
    f.close()

    return content


class TableParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.in_td = False
        self.in_tr = False
        self.found_start = False
        self.collected = ""
        self.result = []
        self.headers = []

    def handle_starttag(self, tag, attrs):
        if tag == 'td':
            self.in_td = True
        if tag == 'tr':
            self.in_tr = True

    def handle_endtag(self, tag):
        if tag == 'tr':
            self.in_tr = False

            if self.found_start:
                try:
                    if int(self.collected.split(' ')[0]) > 0:
                        data_to_append = self.collected[:-1].split("|")
                        record_dict = {}

                        for i in range(0, len(data_to_append)):
                            record = data_to_append[i]
                            header_name = self.headers[i]
                            record_dict[header_name] = record

                        self.result.append(record_dict)
                except:
                    pass
            else:
                self.result.append(self.collected)

            self.collected = ""

        if tag == 'td':
            self.in_td = False
            if self.in_tr:
                self.collected += '|'

    def handle_data(self, data):
        if 'Staro stanje' in data:
            # last result data contains column names
            self.headers = self.result[-1][:-1].split("|")

            self.found_start = True
            self.result.clear()

        if self.in_td and self.in_tr:
            self.collected += data.strip() + " "


def parse_data(header_labels, data):
    global client_dict
    global errors

    client_name_label = None
    for label in header_labels:
        if "Primalac" in label:
            client_name_label = label
            break

    if client_name_label is None:
        errors.append(data)
    else:
        # We now know how to recognize client name
        for record in data:
            client_name = record[client_name_label]
        try:
            client_dict[client_name].append(record)
        except:
            client_dict[client_name] = record


def out_data():
    global client_dict
    global errors

    for name in client_dict:
        data_list = client_dict[name]
        print(name)
        for record in data_list:
            print("\t", record)


for file in list_files(current_path):
    fc = read_file(file)
    file_parser = TableParser()
    file_parser.feed(fc)

    headers = file_parser.headers

    for text in file_parser.result:
        parse_data(headers, text)

# out_data()
