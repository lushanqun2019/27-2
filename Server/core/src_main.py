import socket
import time
from conf import setting
from db import models, db_handler


def register(conn, message):
    status, name, password = message.split('|')
    # password = server_interface.get_file_md5(password)
    if status == '1':  # 管理员注册
        now_role = models.Admin(name, password)
    else:
        now_role = models.User(name, password)
        print(now_role.name)
    is_success = db_handler.create_user(now_role, int(status))
    msg = str(is_success) + '|0'
    msg = msg.encode('utf-8')
    conn.send(msg)


def login(conn, message):
    status, name, password = message.split('|')
    status = int(status)
    now_user = db_handler.select_user(name, status)
    is_success = 0
    is_member = 0
    if status == 0:
        is_member = now_user.is_member
    if now_user:
        if now_user.password == password:
            is_success = 1
    msg = str(is_success) + '|' + str(is_member)
    msg = msg.encode('utf-8')
    conn.send(msg)


def upload_file_for_admin(conn, message):  # 接收文件
    admin_name, file_name, file_size, file_md5 = message.split('|')
    file_size = int(file_size)
    flag = db_handler.upload_file_for_admin(conn, admin_name, file_name, file_size, file_md5)
    if flag:
        print('{} upload {}, the md5 is {}'.format(admin_name, file_name, file_md5))
    else:
        print('{} upload {} failed}'.format(admin_name, file_name))


def upload_file_for_user(conn, message):  # 接收文件
    user_name, file_name, file_size, file_md5, upload_file_path = message.split('|')
    file_size = int(file_size)
    flag = db_handler.upload_file_for_user(conn, user_name, file_name, file_size, file_md5, upload_file_path)
    if flag:
        print('{} upload {}, the md5 is {}'.format(user_name, file_name, file_md5))
    else:
        print('{} upload {} failed}'.format(user_name, file_name))


def download_file_for_user(conn, message):
    user_name, user_is_member = message.split('|')
    user_is_member = int(user_is_member)
    user_file_list = db_handler.show_user_files(user_name)
    online_file_list = db_handler.show_online_files()
    if (not user_file_list) and (not online_file_list):
        msg = '0||||'.encode('utf-8')
        conn.send(msg)
    else:
        msg = '1||' + '|'.join([i.name for i in user_file_list]) + '||' + '|'.join([i.name for i in online_file_list])
        # 用户不仅可下载自己网盘上的文件，还可下载管理员上传的文件
        msg = msg.encode('utf-8')
        conn.send(msg)
    data = conn.recv(1024)
    data = data.decode('utf-8')
    flag, file_select = data.split('|')
    if flag == '0':  # 用户申请下载自己网盘上的内容
        file_select = user_file_list[int(file_select)]
    else:
        file_select = online_file_list[int(file_select)]
    db_handler.download_file(conn, file_select, user_is_member)


def join_member(conn, user_name):
    db_handler.join_member(user_name)
    msg = '1'.encode('utf-8')
    conn.send(msg)


def time_synchronization(conn, server_name):
    fmt = '%Y/%m/%d %X'
    time_now = time.strftime(fmt)
    conn.send(time_now.encode('utf-8'))  # 给子服务器发送信息


func_dict = {
    '1': register,
    '2': login,
    '3': download_file_for_user,  # 用户下载文件
    '4': upload_file_for_admin,  # 管理员上传文件
    '5': upload_file_for_user,  # 用户上传文件
    '6': join_member,
    '7': time_synchronization
}


def run():
    sk = socket.socket()
    sk.bind(setting.SERVER_ADDRESS_MAIN)
    sk.listen(3)
    while True:
        conn, addr = sk.accept()
        while True:
            data = conn.recv(1024)
            data = data.decode('utf-8')
            flag, remain_msg = data.split('||')  # 识别用户发来的信息类型，1为申请注册，2为申请登录，3为用户申请下载
            # 文件，4为管理员上传文件， 5为普通用户上传文件， 6为用户开通会员请求， 7为其他服务器的时间同步请求
            func_dict[flag](conn, remain_msg)
            break
        conn.close()
    sk.close()
