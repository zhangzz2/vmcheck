# vmcheck

检查到节点异常后，更新数据库vm的状态为stopped

工作原理：


    在zstack管理节点上周期检查当前虚拟机的状态，
    如果数据库中虚拟机的状态是running， 但是通过ping，发现所在的物理机，连续5分钟不通的话，
    就把该虚拟机的状态设置为Stopped. 这个功能是manager这个模块是实现的。

    在计算节点上，会周期的检查该节点是否fense。如果连续5分钟fense的话，把该节点上的虚拟机都杀掉。
    这个功能是agent模块来实现的。



部署方式：


    1，下载vmcheck安装包。并在集群内所有节点都执行 python setup.py install
    2，在zstack manager 节点执行 vmcheck-ctl --add_admin_cron， 
    3, 在计算节点执行 vmcheck-ctl --add_agent_cron 
    4，完成部署


备注：


    放到crontab里面并不是说要依赖cron来周期执行。
    放到里面是为了确保vmcheck_manager 和 vmcheck_agent 退出后，可以依靠cron再次启动起来。



运行日志:


    /var/log/vmcheck_admin.log 
    /var/log/vmcheck_agent.log 


命令行：


    [root@node228 vmcheck]# vmcheck-ctl -h
    Usage: vmcheck-ctl [options] arg1 arg2

    Options:
    -h, --help        show this help message and exit
    --add_admin_cron  add vmcheck_admin to crontab
    --del_admin_cron  del vmcheck_admin from crontab
    --add_agent_cron  add vmcheck_agent to crontab
    --del_agent_cron  del vmcheck_agent from crontab
    [root@node228 vmcheck]# 
