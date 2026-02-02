#!/usr/bin/python
# -*- encoding=utf8 -*-

import os
import subprocess
import signal
import threading
import time


def system(my_cmd):
    """The sdtout and stderr will be the default."""

    rc, stdout, stderr = sh(my_cmd)
    return rc


def sh(cmd, raise_exception=False, timeout=None):
    """Execute a shell command, return the result.
    he stdout and stderr are collected and can be read later.
    Run the cmd and return the (returncode, stdout, stderr).
    raise_exception: if raise_exception is True, if the returncode is not 0,
                     an exception that contains the stdout and the stderr 
                     information will be raised.
    Args:
        cmd: A shell command that you want to run. For example 'ls'.
        raise_exception: If raise_exception is True, this function will raise
            an exception if the exit code of the shell command is not 0.
        timeout: If the timeout is not None, and the the shell command can not 
            be finished during the timeout, the child shell process will be 
            terminated.
    Returns:
        A tuple with 3 elements will be returned. The tuple contains:
        (exit code of the command, the standard output of the command, 
        the stdandard error ouput of the comamd).
    """

    if timeout is None:
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        stdoutdata, stderrdata = p.communicate()
        if raise_exception and p.returncode != 0:
            raise Exception("Execute cmd:%s failed.\nstdout:%s\nstderr:%s" %
                            (cmd, stdoutdata, stderrdata))
        return p.returncode, stdoutdata, stderrdata
    else:
        p = None
        result = [None, 0, "", "Timeout"]

        def target(result):
            p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, preexec_fn=os.setsid)
            result[0] = p
            (result[2], result[3]) = p.communicate()
            result[1] = p.returncode
            if raise_exception and p.returncode != 0:
                raise Exception("Execute cmd:%s failed.\nstdout:%s\nstderr:%s" %
                                (cmd, result[2], result[3]))

        thread = threading.Thread(target=target, kwargs={'result': result})
        thread.start()
        thread.join(timeout)
        if thread.is_alive():
            # Timeout
            p = result[0]
            wait_time = 5
            while p is None:
                time.sleep(1)
                p = result[0]
                wait_time -= wait_time
                if wait_time == 0:
                    exit(1)
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            thread.join()
            if raise_exception:
                raise Exception("Execute cmd:%s failed, timeout:%d." % (
                    cmd, timeout))
        return result[1], result[2].encode('unicode-escape') \
            .decode('unicode-escape'), result[3].encode('unicode-escape') \
                   .decode('unicode-escape')


def ssh(host, cmd):
    """Execute a command over ssh. 
    Returns
        The (result code, stdout, stderr).
    """

    cmd_separator = "'"
    if '"' in cmd and "'" in cmd:
        return 1, '', """cmd:%s can not contain both " and '"""
    if "'" in cmd:
        cmd_separator = '"'

    ssh_cmd = "ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no -o \
           TcpKeepAlive=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3\
            -o BatchMode=yes %s %s%s%s" % (host, cmd_separator, cmd,
                                           cmd_separator)

    return sh(ssh_cmd)


def ssh_with_timeout(host, cmd, timeout):
    """
    执行ssh命令
    :param host:
    :param cmd:
    :param timeout: 超时时间
    :return:
    """

    cmd_separator = "'"
    if '"' in cmd and "'" in cmd:
        return 1, '', """cmd:%s can not contain both " and '"""
    if "'" in cmd:
        cmd_separator = '"'

    ssh_cmd = "ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no -o \
           TcpKeepAlive=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3\
            -o BatchMode=yes %s %s%s%s" % (host, cmd_separator, cmd,
                                           cmd_separator)

    return sh(ssh_cmd, timeout=timeout)


def ssh2(host_ips, cmd):
    """Execute a command over ssh on a host.

    Args:
        cmd: The shell command to be executed on hosts.
        host_ips: A list of IPs of the destination host.

    Returns:
        A tuple of (result_code, stdout, stderr).      
        If all IPs in host_ips are unavailable, then the result of cmd on last 
        host is returned. 
    """

    available_ips = [ip for ip in host_ips if ping(ip)]
    if len(available_ips) == 0:
        return ssh(host_ips[-1], cmd)
    else:
        return ssh(available_ips[0], cmd)


def ssh2_with_timeout(host_ips, cmd, timeout):
    """
    执行ssh命令
    :param host_ips:
    :param cmd:
    :param timeout: 超时时间
    :return:
    """

    available_ips = [ip for ip in host_ips if ping(ip)]
    if len(available_ips) == 0:
        return ssh_with_timeout(host_ips[-1], cmd, timeout)
    else:
        return ssh_with_timeout(available_ips[0], cmd, timeout)


def ssh3(user, host, cmd):
    """Execute a command over ssh.
        Args:
            user: login user
            host:login ip
            cmd: run cmd
        Returns
            The (result code, stdout, stderr).
        """

    cmd_separator = "'"
    if '"' in cmd and "'" in cmd:
        return 1, '', """cmd:%s can not contain both " and '"""
    if "'" in cmd:
        cmd_separator = '"'

    user_at = user + "@" if user != "" else ""
    ssh_cmd = "ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no -o \
               TcpKeepAlive=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3\
                -o BatchMode=yes %s%s %s%s%s" % (user_at, host, cmd_separator,
                                                 cmd, cmd_separator)

    return sh(ssh_cmd)


def gen_scp_cmd(src_host, src_file_or_dir, dest_host, dest_path,
                src_user, dest_user, *args):
    """
    拼接scp命令
    :param src_host:
    :param src_file_or_dir:
    :param dest_host:
    :param dest_path:
    :param src_user:
    :param dest_user:
    :param args:
    :return:
    """

    all_args = args
    # 如果是目录则加上“-r”参数
    if os.path.isdir(src_file_or_dir):
        all_args = ["-r"] + list(args)
    arg_list = " ".join(all_args)

    # 没有指定源host时，默认为本机
    if src_host == "":
        scp_cmd = "scp %(arg_list)s" \
                  " %(src_file_or_dir)s" \
                  " %(dest_user)s@%(dest_host)s:%(dest_path)s" % {
                      'arg_list': arg_list, 'src_file_or_dir': src_file_or_dir,
                      'dest_user': dest_user, 'dest_host': dest_host,
                      'dest_path': dest_path}
    # 没有指定目的host时，默认为本机
    elif dest_host == "":
        scp_cmd = "scp %(arg_list)s" \
                  " %(src_user)s@%(src_host)s:%(src_file_or_dir)s" \
                  " %(dest_path)s" % {
                      'arg_list': arg_list, 'src_user': src_user,
                      'src_host': src_host, 'src_file_or_dir': src_file_or_dir,
                      'dest_path': dest_path}
    else:
        scp_cmd = "scp %(arg_list)s " \
                  "%(src_user)s@%(src_host)s:%(src_file_or_dir)s" \
                  " %(dest_user)s@%(dest_host)s:%(dest_path)s" % {
                      'arg_list': arg_list, 'src_user': src_user,
                      'src_host': src_host, 'src_file_or_dir': src_file_or_dir,
                      'dest_user': dest_user, 'dest_host': dest_host,
                      'dest_path': dest_path}
    return scp_cmd


def gen_base_scp_cmd(src_host, src_file_or_dir, dest_host, dest_path,
                     src_user="root", dest_user="root"):
    """
    生成基础scp命令
    :param src_host:
    :param src_file_or_dir:
    :param dest_host:
    :param dest_path:
    :param src_user:
    :param dest_user:
    :param args:
    :return:
    """
    # 限速100MB（scp -l 的单位为Kbit/s）
    # BatchMode=yes： 在没有配置无密访问时直接报错而不是卡住
    base_args = ["-l", str(100 * 1024 * 8), "-o", "BatchMode=yes"]
    return gen_scp_cmd(src_host, src_file_or_dir, dest_host, dest_path,
                       src_user, dest_user, *base_args)


def scp(file_or_dir, dest_host, dest_path):
    """Copy a file or directory to remote host through scp command."""

    my_cmd = gen_base_scp_cmd("", file_or_dir, dest_host, dest_path)
    return system(my_cmd)


def scp2(file_or_dir, dest_host_ips, dest_path):
    """Another version of scp, the destination can have more than one 
    IP, and this function will copy the file or directory to the 
    destination throuth any of the avaliable ip.

    Args:
        file_or_dir: A file for dir path.
        dest_host_ips: The IPs of the destination host.
        dest_path: The path on the destination host that the file 
                   should be copied.

    Returns:
        0 if succeed, otherwise a non-zero value is returned.
    """

    available_ips = [ip for ip in dest_host_ips if ping(ip)]
    if len(available_ips) == 0:
        return 1
    else:
        return scp(file_or_dir, available_ips[0], dest_path)


def scp_remote_to_local(remote_host_ips, remote_path, local_path):
    """
    Copy file or dir in remote host to local path.
    Args:
        local_path: A file for dir path.
        remote_host_ips: The IPs of the remote host.
        remote_path: The path on the remote host that the file
                   should be copied.

    Returns:
        0 if succeed, otherwise a non-zero value is returned.
    """

    available_ips = [ip for ip in remote_host_ips if ping(ip)]
    if len(available_ips) == 0:
        return 1
    scp_cmd = gen_base_scp_cmd(available_ips[0], remote_path, "", local_path)
    return system(scp_cmd)


def rsync(file_or_dir, dest_host, dest_path, exclude_pattens=None):
    """
    rsync file or dir
    :param exclude_pattens: 排除的文件的模式
    :param file_or_dir:
    :param dest_host:
    :param dest_path:
    :return:
    """
    if exclude_pattens is None:
        exclude_pattens = []

    if not os.path.exists(file_or_dir):
        print '%s does not exist.' % file_or_dir
        return 1

    exclude = " ".join(["--exclude=%s" % patten for patten in exclude_pattens])
    my_cmd = "rsync -av -e ssh %s %s %s:%s" % (
        exclude, file_or_dir, dest_host, dest_path)
    return sh(my_cmd)


def rsync2(file_or_dir, dest_host_ips, dest_path, exclude_pattens=None):
    """
    rsync with ips
    :param dest_host_ips:
    :param file_or_dir:
    :param dest_path:
    :param exclude_pattens:
    :return:
    """
    if exclude_pattens is None:
        exclude_pattens = []

    available_ips = [ip for ip in dest_host_ips if ping(ip)]
    if len(available_ips) == 0:
        return 1, "no available ip", "no available ip"
    else:
        return rsync(file_or_dir, available_ips[0], dest_path, exclude_pattens)


def scp_with_error_msg(file_or_dir, dest_host, dest_path):
    """Copy a file or directory to remote host through scp command,with error
    msg """

    my_cmd = gen_base_scp_cmd("", file_or_dir, dest_host, dest_path)
    return sh(my_cmd)


def scp2_with_error_msg(file_or_dir, dest_host_ips, dest_path):
    """Another version of scp with error msg, the destination can have more than one 
    IP, and this function will copy the file or directory to the 
    destination throuth any of the avaliable ip.

    Args:
        file_or_dir: A file for dir path.
        dest_host_ips: The IPs of the destination host.
        dest_path: The path on the destination host that the file 
                   should be copied.

    Returns:
        0 if succeed, otherwise a non-zero value is returned.
    """

    available_ips = [ip for ip in dest_host_ips if ping(ip)]
    if len(available_ips) == 0:
        return 1
    else:
        return scp_with_error_msg(file_or_dir, available_ips[0], dest_path)


def scp3(file_or_dir, user_name, dest_hosts, dest_path):
    """Another version of scp, the dest_hosts should a list of IPs,
    and this function will copy the file or directory to all of the 
    destinations. 

    Args:
        file_or_dir: A file for dir path.
        user_name:user
        dest_hosts: A list of IPs, each IP represents a host.
        dest_path: The path on the destination host that the file 
                   should be copied.

    Returns:
        0 if succeed, otherwise a non-zero value is returned.
    """
    scp_cmds = [gen_base_scp_cmd("", file_or_dir, dest_host, dest_path, \
                                 dest_user=user_name) for dest_host in
                dest_hosts]
    cmd = ";".join(scp_cmds)

    return system(cmd)


def scp3_with_error_msg(file_or_dir, user_name, dest_hosts, dest_path):
    """Another version of scp, the dest_hosts should a list of IPs,
    and this function will copy the file or directory to all of the
    destinations.

    Args:
        file_or_dir: A file for dir path.
        user_name:user
        dest_hosts: A list of IPs, each IP represents a host.
        dest_path: The path on the destination host that the file
                   should be copied.

    Returns:
        0 if succeed, otherwise a non-zero value is returned.
    """
    scp_cmds = [gen_base_scp_cmd("", file_or_dir, dest_host, dest_path, \
                                 dest_user=user_name) for dest_host in
                dest_hosts]
    cmd = ";".join(scp_cmds)

    return sh(cmd)


def scp_src_to_remote(src_ips, src_path, dest_host_ips, dest_path):
    """
        Another version of scp, the dest_hosts should a list of IPs,
        and this function will copy the remote file or directory to all of the 
        destinations
        eg: scp root@IP:src_ip:src_path root@IPs:dest_path

        Args:
        src_ip: A ip for src dir path.
        src_path: the path of the src file
        dest_host_ips: A list of IPs, each IP represents a host.
        dest_path: The path on the destination host that the file
                   should be copied.

    Returns:
        0 if succeed, otherwise a non-zero value is returned.
    """

    available_src_ips = [ip for ip in src_ips if ping(ip)]
    if len(available_src_ips) == 0:
        return 1

    available_ips = [ip for ip in dest_host_ips if ping(ip)]
    if len(available_ips) == 0:
        return 1
    else:
        scp_cmd = gen_base_scp_cmd(available_src_ips[0], src_path,
                                   available_ips[0], dest_path)
        return system(scp_cmd)


def execute_file(host, file, dest_dir='/tmp'):
    """Execute a file on remote node. 
    
    Returns:
        The (result code, stdout, stderr).
    """

    rc = scp(host, file, dest_dir)
    if rc:
        print 'Scp file:%s to host:%s failed.' % (file, host)
        return (rc, "", "")

    filename = os.path.basename(file)
    my_cmd = '%s/%s' % (dest_dir, filename)
    (rc, stdout, stderr) = ssh(host, my_cmd)

    # Delete the file on remote node.
    my_cmd = 'rm -rf %s/%s' % (dest_dir, filename)
    ssh(host, my_cmd)

    return (rc, stdout, stderr)


def gen_ping_cmd(ip):
    """Generate a ping command, which can be used to check whether the 
    ip can be reached.
    """

    return "ping -i 0.2 -w 2 -W 2 -c 5 -q %s" % ip


def ping(ip):
    """If the ip can be successfully reached by ping command, return 
    True, otherwise return False.
    """

    cmd = gen_ping_cmd(ip)
    rc = system(cmd)
    if rc == 0:
        return True
    else:
        return False
