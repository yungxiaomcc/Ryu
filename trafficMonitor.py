#!/usr/bin/python
#-*- coding: UTF-8 -*-
'''
1.如何通过实现多线程
2.获取流统计信息，获取端口统计信息

{
   "OFPPortStatsReply": {
      "body": [
         {
            "OFPPortStats": {
               "collisions": 0,
               "duration_nsec": 151000000,
               "duration_sec": 163,
               "port_no": 4294967294,
               "rx_bytes": 0,
               "rx_crc_err": 0,
               "rx_dropped": 6,
               "rx_errors": 0,
               "rx_frame_err": 0,
               "rx_over_err": 0,
               "rx_packets": 0,
               "tx_bytes": 0,
               "tx_dropped": 0,
               "tx_errors": 0,
               "tx_packets": 0
            }
         },
         {
            "OFPPortStats": {
               "collisions": 0,
               "duration_nsec": 153000000,
               "duration_sec": 163,
               "port_no": 1,
               "rx_bytes": 1556,
               "rx_crc_err": 0,
               "rx_dropped": 0,
               "rx_errors": 0,
               "rx_frame_err": 0,
               "rx_over_err": 0,
               "rx_packets": 20,
               "tx_bytes": 4276,
               "tx_dropped": 0,
               "tx_errors": 0,
               "tx_packets": 39
            }
         },
         {
            "OFPPortStats": {
               "collisions": 0,
               "duration_nsec": 153000000,
               "duration_sec": 163,
               "port_no": 2,
               "rx_bytes": 1556,
               "rx_crc_err": 0,
               "rx_dropped": 0,
               "rx_errors": 0,
               "port_no": 1,
               "rx_bytes": 1556,
               "rx_crc_err": 0,
               "rx_dropped": 0,
               "rx_errors": 0,
               "rx_frame_err": 0,
               "rx_over_err": 0,
               "rx_packets": 20,
               "tx_bytes": 4276,
               "tx_dropped": 0,
               "tx_errors": 0,
               "tx_packets": 39
            }
         },


'''
from operator import attrgetter

import simple_switch13
import json
from ryu.lib import hub
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub

class Monitor13(simple_switch13.Swich13):

    def __init__(self, *args, **kwargs):
        super(Monitor13, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)


    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(50)



    def _request_stats(self, datapath):
        self.logger.debug("send stats request: %016x", datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        # 构建 发送流表统计数据的请求
        req = parser.OFPFlowStatsRequest(datapath)
        datapath.send_msg(req)
        # 构建 端口统计数据的请求
        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    # 处理 流表统计信息回复消息
    @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    def _flow_stats_reply_handler(self, ev):
        #body = ev.msg.body

        self.logger.info('%s', json.dumps(ev.msg.to_jsondict(), ensure_ascii=True,
                                          indent=3, sort_keys=True))
    # 处理 端口统计信息回复消息
    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        self.logger.info('%s', json.dumps(ev.msg.to_jsondict(), ensure_ascii=True,
                                          indent=3, sort_keys=True))

    # 维护 监控的交换机列表，当有新的交换机加入，注册；交换机断开，将交换机从监控列表中移除
    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug("register datapath: %016x", datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug("unregister datapath: %016x", datapath.id)
                del self.datapaths[datapath.id]
