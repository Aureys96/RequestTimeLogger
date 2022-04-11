import os
import re
import json
from datetime import datetime
import matplotlib.pyplot as plt

pattern = "(.*http-outgoing-.*(\"GET | \"POST).*)|(.*http-outgoing-.* << \"HTTP\\/1.1.*)"
format = "%Y-%m-%d %H:%M:%S,%f"


def read_large_file(file_handler):
    for line in file_handler:
        yield line


def find_http_connection_number(line):
    outgoing_start_index = line.find('http-outgoing-')
    return line[outgoing_start_index + 14:line.find(' ', outgoing_start_index)]


def find_sib_async_thread_number(line):
    thread_start_number = line.find('sib-async [')
    return line[thread_start_number + 11: line.find(']', thread_start_number)]


def get_id(line):
    if 'sib-async' in line:
        return '{}-{}'.format(find_sib_async_thread_number(line), find_http_connection_number(line))

    return find_http_connection_number(line)


def get_log_time(line):
    return line[:23]


def get_time_delta(request_id, log_time, data_table):
    return datetime.strptime(log_time, format) - datetime.strptime(data_table[request_id]['sending_time'], format)


def fill_data_table(line, data_table):
    request_id = get_id(line)
    log_time = get_log_time(line)
    if request_id in data_table:
        time_delta = get_time_delta(request_id, log_time, data_table)
        data_table[request_id].update({
            'reply_time': log_time,
            'request_time': str(time_delta)[:-3]
        })
    else:
        data_table[request_id] = {'sending_time': log_time}


def create_plot(data_table):
    x_axis = []
    y_axis = []

    for value in data_table.values():
        x_axis.append(datetime.strptime(value['sending_time'], format))
        y_axis.append(datetime.strptime(value['request_time'], '%H:%M:%S.%f'))

    f = plt.figure()
    f.set_figwidth(20)
    f.set_figheight(10)

    plt.plot(
        x_axis, y_axis
    )
    #x_ranger = [datetime.strptime('{}:{}:{}'.format(0, 0, i*5), '%H:%M:%S') for i in range(12)]

    plt.title('Время запроса/время дня')

    plt.savefig("date-request_plot.png")


with os.scandir('.') as entries:
    for entry in entries:
        if entry.is_file():
            if '.log' not in entry.name:
                continue
            print('Start processing on ' + entry.name)
            with open(entry, 'r') as r:
                regexp = re.compile(pattern)
                data_table = {}
                for line in read_large_file(r):
                    if regexp.match(line):
                        fill_data_table(line, data_table)

                print(json.dumps(data_table, indent=4))

                create_plot(data_table)
