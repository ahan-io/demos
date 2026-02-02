# encoding=utf8

import os
import re
import multiprocessing
import traceback
import json
import socket
import sys
import time
import shell


AUTO_MOUNT_OPEN = 1
AUTO_MOUNT_CLOSE = 0
LSOF_TIME_OUT = 15


def _warp_fun(*args, **kwargs):
    index = args[0]
    real_func = args[1]
    real_arg = args[2]
    try:
        if type(real_arg) == type([]):
            result = real_func(*real_arg, **kwargs)
        else:
            result = real_func(real_arg, **kwargs)
    except:
        sys.stderr.write(traceback.format_exc())
        return None
    return index, result


def parallel_execute(func, args=[], kwargs={}):
    """Execute the function parallelly.
    
    Args:
        func: the function that will be executed.
        args: a list, each element will be passed as an argument to the function.
        kwargs: a dict which will be passed to the function.

    Returns:
        a list, each element in the list is a result of a function.
   """

    min_num = min((len(args), 100))
    pool = multiprocessing.Pool(min_num)
    results = []
    task_list = []
    i = 0
    for a in args:
        t = pool.apply_async(_warp_fun, args=[i, func, [a]], kwds=kwargs)
        task_list.append(t)
        i += 1
    pool.close()
    pool.join()
    for t in task_list:
        results.append(t.get())
    # Check error.
    for r in results:
        if r is None:
            raise Exception('Some error happens, see detail message in log.')
    results = [r[1] for r in results]
    return results


def parse_string_to_dic(input_str, sep1='#', sep2=':'):
    """Parse the input string, return a dic object.
    The input should be string like:
    key1:value1#key2:value2...
    Otherwise, the sep1 and spe2 should be set.
    """

    ret = {}
    key_values = input_str.split(sep1)
    for k_v in key_values:
        temp = k_v.split(sep2)
        if len(temp) < 2:
            raise Exception("The format of input:%s is incorrect." % input_str)
        if ret.get(temp[0]) != None:
            raise Exception("Duplicate key in input:%s" % input_str)
        ret[temp[0]] = sep2.join(temp[1:])
    return ret


def gen_ping_cmd(ip):
    """Generate a ping command, which can be used to check whether the ip can 
be reached."""

    return "ping -i 0.2 -w 2 -W 2 -c 5 -q %s" % ip


def check_ip_avaliable(ip):
    """check ip if avaliable"""

    rc, stdout, stderr = shell.sh(gen_ping_cmd(ip))
    if rc != 0:
        return False
    return True


def get_avaliable_ips(ips):
    """get avaliable ip"""

    i = 0
    is_avaliables = parallel_execute(check_ip_avaliable, ips)
    for is_avaliable in is_avaliables:
        if is_avaliable:
            i += 1
        else:
            ips.remove(ips[i])
            continue
    return ips


def get_cli_dir():
    """Get the parent directory of CLI directory."""
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    cli_dir = os.path.dirname(os.path.dirname(os.path.dirname(cur_dir)))
    return cli_dir


def get_files_of_dir(dir_path):
    """Get file under the specified directory.
    """

    files = [f for f in os.listdir(dir_path) if
             os.path.isfile(os.path.join(dir_path, f))]
    return files


def gen_tar_command(original_file_path):
    return 'tar xvf %s' % original_file_path


def copy_package_to_remote(host_ips, dest_path):
    """Copy the ParaStor package to remote host.

    Returns:
        If failed, an exception will be raised.
    """

    cli_dir = get_cli_dir()
    if cli_dir.startswith(settings.PARASTOR_HOME):
        package_dir = settings.PARASTOR_SOFTWARE_DIR
        packages = get_files_of_dir(package_dir)
        # Just choose the first package file in the package directory.
        # In fact, there should be only one package file in the directory.
        package_path = packages[0]

        # Scp package to remote host.
        rc = shell.scp2(package_path, host_ips, dest_path)
        if rc != 0:
            raise Exception("Copy package from %s to %s:%s failed." % (
                package_path, ' '.join(host_ips), dest_path))
        # Untar the package
        tar_command = gen_tar_command(dest_path + "/"
                                      + package_path.split('/')[-1])
        (rc, stdout, stderr) = shell.ssh2(tar_command, host_ips)
        if rc != 0:
            raise Exception('Untar the package failed: %s \n %s' % (stdout,
                                                                    stderr))
        return
    else:
        package_dir = get_cli_dir()
        rc = shell.scp2(package_dir, host_ips, dest_path)
        if rc != 0:
            raise Exception('Copy package directory (%s) to remote host \
failed:%s\n%s' % (package_dir, ' '.join(host_ips), dest_path))
        return


def mkdir_remote(host_ips, dir):
    """Create the directory on remote host.

    Returns:
        None

    Raises:
        If failed, an exception will be raised.
    """

    my_cmd = 'mkdir -p %s' % dir
    rc, stdout, stderr = shell.ssh2(host_ips, my_cmd)
    if rc != 0:
        raise Exception("Make directory %s on %s failed:%s,%s" % (
            dir, ' '.join(host_ips), stdout, stderr))


def copy_tools_to_remote(host_ips, dest_path):
    """Copy the ParaStor CLI and tools directories to remote host.

    Returns:
        None

    Raises:
        If failed, an exception will be raised.
    """

    mkdir_remote(host_ips, dest_path)
    dest_dirs = [dest_path, '%s/tools' % dest_path, '%s/conf' % dest_path]
    for dest_dir in dest_dirs:
        mkdir_remote(host_ips, dest_dir)

    cli_parent_dir = get_cli_dir()
    src_dirs = ['%s/cli' % cli_parent_dir,
                '%s/tools/hardware' % cli_parent_dir,
                '%s/conf/hardware_conf' % cli_parent_dir,
                ]
    # 排除一些无用的其比较大的文件
    excludes = [r"*jnl_devformat", r"*obs_addldisk", r"*obs_format"]

    for src_dir, dest_dir in zip(src_dirs, dest_dirs):
        log.info("src %s, dest %s" % (src_dir, dest_dir))
        rc, stdout, stderr = shell.rsync2(src_dir, host_ips, dest_dir, excludes)
        if rc != 0:
            raise Exception(
                "Copy directory from %s to %s:%s failed, stdout: %s, stderr: %s " % (
                    src_dir, ' '.join(host_ips), dest_dir, stdout, stderr))


def get_package_name():
    """Returns the ParaStor software package name(without the postfix).

    An exception will be raised if failed.
    """

    cli_dir = get_cli_dir()
    log.info("cli_dir:%s" % cli_dir)
    # 安装包直接放在/home目录下时，解压后的目录与cli_dir有相同前缀/home/parastor，
    # 需要判断/home下的parastor是系统目录还是安装包目录
    if cli_dir.startswith(settings.PARASTOR_HOME) \
            and cli_dir.strip().split('/')[2] == \
            settings.PARASTOR_HOME.strip().split('/')[2]:
        package_dir = settings.PARASTOR_SOFTWARE_DIR
        package_name = os.listdir(package_dir)[0]
        if '.tar.xz' in package_name:
            return package_name[:-7]  # Remove the '.tar.gz'
        return package_name
    else:
        package_dir = cli_dir
        package_name = package_dir.strip().split('/')[-2]
        return package_name


def get_local_version():
    """Return the version of the installed ParaStor software on local
    host. This is implemented by finding the version in node.xml. If
    no such file is found or the version can not be found in node.xml,
    -1 will be returned.
    """

    if not os.path.exists(settings.PARASTOR_CONF_LOCAL_NODE):
        return -1
    my_cmd = 'grep version %s ' % settings.PARASTOR_CONF_LOCAL_NODE
    rc, stdout, stderr = shell.sh(my_cmd)
    if rc != 0:
        return -1
    pattern = re.compile('\d+')
    result = pattern.search(stdout)
    if result is None:
        return -1
    try:
        version = int(result.group())
        return version
    except:
        return -1


def get_current_version():
    """Get the version of this script according to the version in package name.
    """

    package_name = get_package_name()
    version_info = package_name.split('-')[-1]
    return version_info



def parse_ip_list(ip_list_str):
    """
    解析ip1,ip2#ip3,ip4 这种形式的IP，返回数组
    Args:
        ip_list_str: 各个节点的IP列表的字符串形式，如 10.0.0.1,20.0.0.1#10.l0.0.2,20.0.0.2

    Returns:
        各个节点的IP列表,如[['10.0.0.1','20.0.0.1'],['10.0.0.2','20.0.0.2']]
        如果解析失败，返回None
    """

    tmp = ip_list_str.split('#')
    mgr_nodes = []
    for t in tmp:
        ips = t.split(',')
        for ip in ips:
            if not validator.is_valid_ip(ip):
                return None
        mgr_nodes.append(ips)
    if len(mgr_nodes) == 0:
        return None
    return mgr_nodes


def log_cron():
    """
    log crontab
    """
    srcfile = '/etc/crontab'
    try:
        with open(srcfile, 'r') as fd:
            # 打印修改完的crontab内容
            log.info("crontab %s" % str(fd.readlines()))
    except Exception as e:
        log.error("log cron failed %s" % str(e))
        print "log cron failed ", str(e)



def get_local_ips():
    """获取所有本地IP（只在Linux下使用，需要ifconifg命令支持）

    Returns:
        IP地址列表
    """
    rc, stdout, stderr = shell.sh(
        "ifconfig |grep 'inet ' |grep -v '127.0.0.1'")
    if rc != 0:
        raise Exception('Cannot get local IP addresses.')

    lines = stdout.strip().split('\n')
    ret = []
    for line in lines:
        # 以空格分隔
        items = line.split(' ')
        # 过滤掉所有空字符串
        items = [x for x in items if x != '']
        # 过滤掉所有不是以数字开头的字符串，剩下的全是IP地址
        items = [re.search("[0-9]+.[0-9]+.[0-9]+.[0-9]+", x).group(0) for x in
                 items if
                 re.search("[0-9]+.[0-9]+.[0-9]+.[0-9]+", x) is not None]
        ret.append(items[0])

    return ret


def get_client_local_ips():
    """获取所有本地IP（只在Linux下使用，需要ifconifg命令支持）
    客户端精简OS(最小OS)不支持ifconfig命令，禁用函数中ifconfig命令。

    Returns:
        IP地址列表
    """
    rc, stdout, stderr = shell.sh(
        "ip addr |grep 'inet ' |grep -v '127.0.0.1'")
    if rc != 0:
        raise Exception('Cannot get local IP addresses.')

    lines = stdout.strip().split('\n')
    ret = []
    for line in lines:
        # 以空格分隔
        items = line.split(' ')
        # 过滤掉所有空字符串
        items = [x for x in items if x != '']
        # 过滤掉所有不是以数字开头的字符串，剩下的全是IP地址
        items = [re.search("[0-9]+.[0-9]+.[0-9]+.[0-9]+", x).group(0) for x in
                 items if
                 re.search("[0-9]+.[0-9]+.[0-9]+.[0-9]+", x) is not None]
        ret.append(items[0])

    return ret


def get_local_ips_with_virtual_ip():
    """获取所有本地IP（只在Linux下使用，需要ifconifg命令支持）

    Returns:
        IP地址列表
    """

    rc, stdout, stderr = shell.sh(
        "ip addr |grep 'inet ' |grep -v '127.0.0.1'")
    if rc != 0:
        raise Exception('Cannot get local IP addresses.')
    lines = stdout.strip().split('\n')
    ret = []
    for line in lines:
        # 以空格分隔
        items = line.split(' ')
        # 过滤掉所有空字符串
        items = [x for x in items if x != '']
        # 过滤掉所有不是以数字开头的字符串，剩下的全是IP地址
        items = [re.search("[0-9]+.[0-9]+.[0-9]+.[0-9]+", x).group(0) for x in
                 items if
                 re.search("[0-9]+.[0-9]+.[0-9]+.[0-9]+", x) is not None]
        ret.append(items[0])
    # pattern = re.compile("inet addr:([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+])")
    # pattern = re.compile("inet addr:([0-9]+.[0-9]+.[0-9]+.[0-9]+)")
    # result_list = re.findall(pattern, stdout)
    return ret


def is_port_avail(port):
    """判断一个端口是否可用

    Args:
        port: 端口号

    Returns:
        可用，返回True，否则返回False
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(('127.0.0.1', port))
    except socket.error as e:
        return False
    sock.close()
    return True


def read_hardware_config(hardware_config_file):
    with open(hardware_config_file, 'r') as f:
        return f.read()


def get_machine_model(hardware_config_file):
    hc = hardware_config.HardwareConfig.parse(
        read_hardware_config(hardware_config_file))
    if (hc.model):
        model = hc.model.strip()
    else:
        model = settings.NODE_MODEL_UNKNOWN
    return model


def get_system_release():
    """ 获取系统的发行版本，比如centos6.5/centos7.2 """
    release_cmd = "lsb_release -a | grep Release | awk -F ' ' '{print $2}'"
    system_cmd = "lsb_release -a | grep 'Distributor ID'|awk -F ' ' '{print $3}'"
    (rc, stdout, stderr) = shell.sh(release_cmd)
    if rc != 0:
        raise Exception('Cannot find the CentOS release.')

    # stdout输出为操作系统版本号，形如“6.5”"10.2.11"，这里我们只要“10.2”，所以先分割后拼接
    release = '.'.join(stdout.strip().split('.')[:2])
    (rc, stdout, stderr) = shell.sh(system_cmd)
    if rc != 0:
        raise Exception('Cannot find the CentOS Distributor ID.')

    # stdout输出为操作系统名字，形如“CentOS”
    system = stdout.strip().lower()
    return system + release


def hint_and_timeit(msg=None):
    """
    打印函数提示信息（默认是函数注释第一行）和统计函数耗时的装饰器
    :param msg:
    :param fn:
    :return:
    """

    def _hint_and_timeit(fn):
        def _wrapper(*args, **kwargs):
            # 默认的提示信息为函数注释的第一行
            doc = ""
            if fn.__doc__ is not None:
                func_docs = fn.__doc__.split("\n")
                if len(func_docs) >= 2:
                    doc = func_docs[1].strip()

            message = msg if msg is not None else doc
            current_time = time.strftime('%Y-%m-%d %H:%M:%S',
                                         time.localtime(time.time()))
            log.info("%s %s %s" % (fn.__name__, message, current_time))
            start = time.time()
            ret = fn(*args, **kwargs)
            log.info("%s finished, cost %s second\n"
                     % (fn.__name__, round(time.time() - start, 2)))
            return ret

        return _wrapper

    return _hint_and_timeit


def get_auto_mount_flag():
    """
    获取系统中配置的自动挂载标记: 0:不自动挂载， 1:自动挂载,
    :return:
    """
    req = {"section": "MGR", "name": "mgcd_auto_mount_flag"}
    try:
        response = network.send_command('get_param',
                                        json.dumps(req, ensure_ascii=False))
        if response.err_no != 0:
            log.error("get auto mount flag failed %d" % response.err_no)
        result = response.result
        parameters = result["parameters"]
        current = parameters[0]["current"]
        return int(current)
    except Exception as e:
        log.error("get auto mount flag failed " + str(e))
        # 如果获取失败，认为自动挂载开启(主要考虑到默认是打开的自动挂载功能)
        return AUTO_MOUNT_OPEN


def set_auto_mount(flag, mgr_ips=None):
    """
    设置自动挂载功能，0：停止自动挂载 1：开启自动挂载
    :return:
    """
    req = {"section": "MGR", "name": "mgcd_auto_mount_flag", "current": flag}
    try:
        response = network.send_command('update_param',
                                        json.dumps(req, ensure_ascii=False),
                                        mgr_ips=mgr_ips)
        if response.err_no != 0:
            log.error("set auto mount flag failed %d" % response.err_no)
    except Exception as e:
        log.error("set auto mount http failed " + str(e))
    return True


def umount_mounted_dirs():
    """
    先umount已经挂载的parastor系统
    :return:
    """

    rc, stdout, stderr = shell.sh("mount | grep 'type parastor'")
    if rc != 0:
        # 没有挂载的parastor系统
        return True

    mount_dirs = []
    parastor_dir_pattern = re.compile(r"^.* on (.*) type parastor .*$")
    for line in stdout.split("\n"):
        match = parastor_dir_pattern.match(line)
        if match:
            mount_dirs.append(match.group(1))

    umount_cmd = " ".join(["umount", "-f"] + mount_dirs)
    log.info("begin to umount %s" % umount_cmd)
    rc, stdout, stderr = shell.sh(umount_cmd)
    if rc != 0:
        log.error("%s failed rc: %d, stdout: %s, stderr: %s"
                  % (umount_cmd, rc, stdout, stderr))
        return False

    return True


# 通过进程名字grep进程号
def get_pid_by_name(pro_name):
    my_cmd = "ps -ef|grep %s|grep -v grep|awk '{print $2}'" % pro_name
    rc, stdout, stderr = shell.sh(my_cmd)
    if rc != 0:
        log.error("my_cmd:%s failed." % my_cmd)
        return False, []
    stdout_lst = stdout.split("\n")[:-1]
    return True, stdout_lst


def filter_space_and_newline(string):
    """
    将字符串转换为没有空格和换行符的数组
    :param string:
    ID   Slot   SN     sizeGB   GTG   temp  CapIsOn   CapEnough   CapVol   CapCharged   ManuId   Type
    0    0    SN2451    16      Y     50       Y       Y            4.3         Y       MID251   AGIGA
    1    1    SN1333    16      Y     50       Y       Y            4.2         Y       MID139   AGIGA
    :return:
    [['ID', 'Slot', 'SN', 'sizeGB', 'GTG', 'temp', 'CapIsOn', 'CapEnough', 'CapVol', 'CapCharged', 'ManuId', 'Type'],
    ['0', '0', 'SN2451', '16', 'Y', '50', 'Y', 'Y', '4.3', 'Y', 'MID251', 'AGIGA'],
    ['1', '1', 'SN1333', '16', 'Y', '50', 'Y', 'Y', '4.2', 'Y', 'MID139', 'AGIGA']]
    """
    # 过滤数组里空字符串
    rst_lst_with_space = filter(None, string.split('\n'))
    rst_lst = [filter(None, i.split(' ')) for i in rst_lst_with_space]
    return rst_lst


def dev_cmd_with_retry(cmd, devname, times=40, interval=3):
    """
    磁盘相关命令的重试方法
    :param cmd:
    :param times:
    :param interval:
    :return:
    [['ID', 'Slot', 'SN', 'sizeGB', 'GTG', 'temp', 'CapIsOn', 'CapEnough', 'CapVol', 'CapCharged', 'ManuId', 'Type'],
    ['0', '0', 'SN2451', '16', 'Y', '50', 'Y', 'Y', '4.3', 'Y', 'MID251', 'AGIGA'],
    ['1', '1', 'SN1333', '16', 'Y', '50', 'Y', 'Y', '4.2', 'Y', 'MID139', 'AGIGA']]
    """

    for i in range(times):
        rc, stdout, stderr = shell.sh(cmd)
        log.info('rc is: %s.' % rc)
        if rc == 0:
            log.info('%s successfully' % cmd)
            break
        log.error('dev cmd %s fail. %d time. stdout:%s stderr%s'
                  % (cmd, i, stdout, stderr))
        time.sleep(interval)
    else:
        execute_lsof_dev_command(devname)
        err_msg = 'dev cmd failed:%s' % cmd
        log.error(err_msg)
        raise Exception(err_msg)


def execute_lsof_dev_command(devname):
    my_cmd = 'lsof %s*' % devname
    log.info("----my_cmd:%s----" % my_cmd)
    rc, stdout, stderr = shell.sh(my_cmd, timeout=LSOF_TIME_OUT)
    log.info(
        "rc:%d, stdout:%s, stderr:%s" % (rc, stdout.split('\n'), stderr))


def create_path_if_not_exist(path):
    create_path_single_list = path.split("/")[1:]
    create_path_single = ""
    for i in create_path_single_list:
        i_path = "/" + i
        create_path_single = create_path_single + i_path
        if not os.path.exists(create_path_single):
            os.mkdir(create_path_single)


def get_package_time_from_path(path):
    """
    get package time from path:
    e.g:
    /home/parastor-3.0.0-centos7.5-tmp_9370c09_20180721_053424-2-1.tar.xz
     => 20180721_053424
    :param path:
    :return:
    """
    parts = path.split("-")[-3].split("_")
    return "_".join(parts[-2:])


def get_param(section, name):
    """
    获取指定参数
    :return:
    """
    req = {"section": section, "name": name}
    response = network.send_command('get_param',
                                    json.dumps(req, ensure_ascii=False))
    if response.err_no != 0:
        err_msg = "get %s:%s failed %d" % (section, name, response.err_no)
        log.error(err_msg)
        raise Exception(err_msg)
    result = response.result
    parameters = result["parameters"]
    current = parameters[0]["current"]
    return current


def get_host_system_release(ip):
    """
    获取对应节点的操作系统版本:centos7.5等
    :param ip:
    :return:
    """
    release_cmd = "lsb_release -a | grep Release"
    system_cmd = "lsb_release -a | grep Distributor"
    (rc, stdout, stderr) = shell.ssh(ip, release_cmd)
    if rc != 0:
        log.error("get release failed %s %s" % (stdout, stderr))
        raise Exception('%s can not find the CentOS release.' % str(ip))
    # stdout输出为操作系统版本号，Release:  7.2.1511 => 7.2
    release = '.'.join(stdout.split(":")[1].strip().split('.')[:2])

    (rc, stdout, stderr) = shell.ssh(ip, system_cmd)
    if rc != 0:
        log.error("get system failed %s %s" % (stdout, stderr))
        raise Exception('%s can not find the CentOS Distributor ID.' % str(ip))
    # stdout输出为操作系统名字，形如“centos” Distributor ID: CentOs => centos
    system = stdout.split(":")[1].strip().lower()
    return system + release


def exchange_mask(mask):
    """
    255.255.192.0 => 18
    :param mask:
    :return:
    """
    count_bit = lambda bin_str: len([i for i in bin_str if i == '1'])
    mask_splited = mask.split('.')
    mask_count = [count_bit(bin(int(i))) for i in mask_splited]
    return sum(mask_count)

def check_int_size(val):
    """
    检查int值是否越界（越界标准以Java int长度为准）
    :param val:
    :return:
    """
    if settings.INT_MAX_VALUE < val:
        err_msg = "input value %s exceed the maximum limit %s" % (val,
                                                                  settings.INT_MAX_VALUE)
        log.error(err_msg)
        raise Exception(err_msg)

def get_master_ips(node_ip):
    """
    根据存储集群中节点ip获取master ip
    :param node_ip:
    :return:
    """
    get_master_cmd = 'pscli --command=get_master'
    rc, stdout, stderr = shell.ssh2([node_ip], get_master_cmd)
    if rc != 0:
        log.error('get master ip failed.stdout:%s,stderr:%s' % (stdout, stderr))
        return []
    response = json.loads(stdout)
    ips = []
    for ip in response['result']['data_ips']:
        ips.append(ip['ip_address'])
    return ips

def get_avaliable_ip(ips):
    """
    get a avaliable ip form ips
    :param ips:
    :return:
    """
    for ip in ips:
        if(check_ip_avaliable(ip)):
            return ip
    return None

def get_zk_hander():
    """
    get zk hander
    :return:
    """
    local_ips = get_local_ips()
    avaliable_local_ip = get_avaliable_ip(local_ips)
    if(avaliable_local_ip is None):
        log.error('get avaliable local ip failed.ips:%s' % (local_ips.join(',')))
        return None
    master_ips = get_master_ips(avaliable_local_ip)
    avaliable_master_ip = get_avaliable_ip(master_ips)
    if(avaliable_master_ip is None):
        log.error('get avaliable master ip failed.ips:%s' % (master_ips.join(',')))
        return None

    zk_handler = ZkHandler(connect_str='%s:2181' % avaliable_master_ip)
    return zk_handler

def sync_buffer_to_disk():
    """
    同步缓存到磁盘
    :param:
    :return:
    """
    cmd = 'sync'
    rc, stdout, stderr = shell.sh(cmd)
    if rc != 0:
        log.error('sync buffer to disk failed.stdout:%s,stderr:%s' % (stdout, stderr));
        return False
    return True


def volume_isbusy(name):
    """
    判断卷是否被占用
    return : True : be used
             Falas: unused
    """
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    tools_dir = os.path.join(cur_dir, '../../../tools')
    cmd = "%s/volume_may_umount -d %s" %(tools_dir, name)
    rc, stdout, stderr = shell.sh(cmd)
    if rc != 0:
        log.info("The volume:%s can be uninstall" %name)
        return False
    # 查看用户态进程信息
    cmd = "ps xlf"
    rc, stdout, stderr = shell.sh(cmd)
    if rc == 0:
        log.info("The node process info:\n%s\n" %stdout)

    # 查看mount 信息
    cmd = "showmount -e 127.0.0.1"
    rc, stdout, stderr = shell.sh(cmd)
    if rc == 0:
        log.info("The node mount export list info:\n%s\n" % stdout)
    cmd = "mount"
    rc, stdout, stderr = shell.sh(cmd)
    if rc == 0:
        log.info("The node mount info info:\n%s\n" % stdout)
    return True


def get_mount_list(umount_list):
    """get mount point"""
    my_cmd = "mount"
    rc, stdout, stderr = shell.sh(my_cmd)
    if rc != 0:
        log.info("cmd(%s) run failed" %my_cmd)
        return 1

    lines = stdout.strip().split('\n')
    for line in lines:
        # 以空格分隔
        items = line.split(' ')
        # 过滤掉所有空字符串
        items = [x for x in items if x != '']
        if items[4] == "parastor":
            umount_list.append(items[2])

    return 0


def mount_volume_check():
    """检测挂载的所有卷信息"""
    umount_list = []
    resoult = 0
    rc = get_mount_list(umount_list)
    if rc != 0:
        log.info("The get umount list failed")
        return 1
    log.info("The umount list:%s" %umount_list)
    for name in umount_list:
        isbusy = volume_isbusy(name)
        if isbusy is True:
            resoult = 1
            log.info("The volume:%s  be used" %name)
            break

    return resoult

