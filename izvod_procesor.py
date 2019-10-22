#!/usr/bin/python3


import os
import sys
#from html.parser import HTMLParser
from HTMLParser import HTMLParser
from collections import OrderedDict
import datetime

# determine if application is a script file or frozen exe
if getattr(sys, 'frozen', False):
    current_path = os.path.dirname(sys.executable)
elif __file__:
    current_path = os.path.dirname(os.path.realpath(__file__))

client_dict = {}
table_header_labels = []
out_file_name = "sortirano.csv"
out_file_path = os.path.join(current_path, out_file_name)
err_file_name = "greske_prilikom_ocitavanja. txt"
err_file_path = os.path.join(current_path, err_file_name)
date_label = None


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

    # f = open(file_path, 'r', encoding=encode)
    f = open(file_path, 'r')
    content = f.read()
    f.close()

    return content


def append_to_header_labels(data, at_beginning=False):
    global table_header_labels

    if len(data) > 1 and data not in table_header_labels:

        if at_beginning:
            table_header_labels = [data] + table_header_labels
        else:
            table_header_labels.append(data)


class TableParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.in_td = False
        self.in_tr = False
        self.found_start = False
        self.collected = ""
        self.headers = []
        self.name_idx = None
        self.last_collected = ""

    def handle_starttag(self, tag, attrs):
        if tag == 'td':
            self.in_td = True
        if tag == 'tr':
            self.in_tr = True
            self.last_collected = self.collected
            self.collected = ""

    def handle_endtag(self, tag):
        global client_dict

        if tag == 'tr':
            self.in_tr = False

            if self.found_start:
                try:
                    if int(self.collected.split(' ')[0]) > 0:
                        data_to_append = self.collected[:-1].split("|")
                        record_dict = {}
                        if self.name_idx is not None:
                            client_name = data_to_append[self.name_idx]
                        else:
                            client_name = "Errors"

                        for i in range(0, len(data_to_append)):
                            record = data_to_append[i]
                            header_name = self.headers[i]
                            record_dict[header_name] = record

                        if client_name in client_dict:
                            client_dict[client_name].append(record_dict)
                        else:
                            client_dict[client_name] = [record_dict]
                except:
                    pass

        if tag == 'td':
            self.in_td = False
            if self.in_tr:
                self.collected = self.collected.strip() + '|'

    def handle_data(self, data):
        global date_label

        if 'Staro stanje' in data:
            # last result data contains column names
            self.headers = self.last_collected[:-1].split("|")

            # Find the name label
            for i in range(0, len(self.headers)):
                label = self.headers[i].strip()
                if "primalac" in label.lower():
                    self.name_idx = i
                    append_to_header_labels(label, at_beginning=True)
                else:
                    if "datum" in label.lower():
                        date_label = label

                    append_to_header_labels(label, at_beginning=False)

            self.found_start = True

        if self.in_td and self.in_tr:
            self.collected += data.strip() + " "


def cleanup_string(text):
    while "  " in text:
        text = text.replace("  ", " ")

    return text


def sort_by_date(record_list):
    global date_label

    record_dict = {}
    date_list = []

    for item in record_list:
        date_time_str = item[date_label].split(" ")[0]
        date_time_obj = datetime.datetime.strptime(date_time_str, '%d.%m.%Y.')
        key = date_time_obj.date()

        try:
            record_dict[key].append(item)
        except:
            record_dict[key] = [item]

    sorted_dict = OrderedDict(sorted(record_dict.items()))

    ret_list = []

    for item in sorted_dict:
        for record in sorted_dict[item]:
            ret_list.append(record)

    return ret_list


def out_data():
    global client_dict
    global table_header_labels
    global out_file_path
    global err_file_path

    lines = []
    row = ""
    errors = []

    for label in table_header_labels:
        row += '"' + label + '",'

    lines.append(row[:-1] + '\n')

    sorted_client_dict = OrderedDict(sorted(client_dict.items()))

    for name in sorted_client_dict:
        data = client_dict[name]

        client_name = '"' + cleanup_string(name) + '",'

        record_list = sort_by_date(data)

        for r in range(0, len(record_list)):
            record = record_list[r]
            row = client_name
            for i in range(1, len(table_header_labels)):
                try:
                    row += '"' + record[table_header_labels[i]].strip() + '",'
                except Exception as e:
                    err_row = '{}' + '\n Original: ' + record + '\n'
                    errors.append(err_row.format(e))

            lines.append(row[:-1] + '\n')

    f = open(out_file_path, 'w')
    f.writelines(lines)
    f.close()

    if len(errors) > 0:
        f = open(err_file_path, 'w')
        f.writelines(errors)
        f.close()


for file in list_files(current_path):
    fc = read_file(file)
    file_parser = TableParser()
    file_parser.feed(fc)

out_data()
