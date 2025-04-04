# -*- coding: utf-8 -*-
"""
@Time    : 2024/12/05 8:20
@Author  : Jason Zou
@Email   : zou.jason@qq.com
@mobile  : 18951631470
"""
import json, time, logging, datetime
from odoo import api, fields, models
from k3cloud_webapi_sdk.main import K3CloudApiSdk
_logger = logging.getLogger(__name__)

# 首先构造一个SDK实例
api_sdk = K3CloudApiSdk()
# config_node:配置文件中的节点名称
api_sdk.Init(config_path='rhino-data-nexus/sdk/conf.ini', config_node='config')
# 此处仅构造保存接口的部分字段数据示例，使用时请参考WebAPI具体接口的实际参数列表
current_time = time.strftime('%Y%m%d%H%M%S', time.localtime())


class WmsShipOrder(models.Model):
    _inherit = 'wms.ship.order'

    # =============== 发料/发货侧单据同步 ===============
    # =============== 发料/发货侧单据同步 ===============
    # =============== 发料/发货侧单据同步 ===============
    def Action_StockOut_Write_Back(self):
        try:
            self.Search_STK_TransferDirect_Write_Back()    # 审核直接调拨单
            self.Search_PRD_PickMtrl_Write_Back()  # 审核生产领料单
        except Exception as e:
            _logger.error('接口返回结果：{}'.format(e))

    # =============== 审核直接调拨单 ===============
    # =============== 审核直接调拨单 ===============
    # =============== 审核直接调拨单 ===============
    def Search_STK_TransferDirect_Write_Back(self):
        """
        本接口用于实现直接调拨单 (STK_STKTRANSFERIN)  的 C审核 功能
        21 中裕软管科技股份有限公司  库表ID：101124
        23 安徽优耐德管道技术有限公司  库表ID：101127

        "and FDocumentStatus = 'B' " "and FCancelStatus = 'A' "
        search_data = stock_in_obj.search([
            ('create_date', '>=', today.strftime('%Y-%m-%d 00:00:00')),
            ('create_date', '<=', today.strftime('%Y-%m-%d 23:59:59')),
            ('SyncState', '=', 1),
            ('DocumentStatus', '=', 'B')
        ])
        :return:
        """
        stock_out_obj = self.env['wms.ship.order']  # 直接调拨单
        # 查数据
        # today = datetime.date.today()
        _logger.info('直接调拨单接口回写--当前时间：{}'.format(datetime.datetime.utcnow() + datetime.timedelta(hours=8)))
        search_data = stock_out_obj.search([('SyncState', '=', 1), ('DocumentStatus', '=', 'B')])
        check_values = []
        result = []
        _logger.info('直接调拨单接口回写--传递数据：'.format(search_data))
        if len(search_data) == 0:
            return
        for line in search_data:
            check_values.append(line.TMBillNo)
        for value in sorted(list(set(check_values))):
            li = stock_out_obj.search([('TMBillNo', '=', value)])
            check_values1 = []
            for l in li:
                check_values1.append(l.SyncState)
            if len(list(set(check_values1))) == 1:
                result.append(l.TMBillNo)
            # 判断AGV是否执行完，搬运完成整单回写提交ERP直接调拨单审核
        _logger.info('直接调拨单接口回写--更新记录：'.format(sorted(list(set(result)))))
        self.Data_StockOut_Write_Back(Numbers=result)    # 批量提交云星空单据审批，变更状态为“C已审批”
        for tmp in result:
            c = stock_out_obj.search([('TMBillNo', '=', tmp)])
            c.write({'DocumentStatus': 'C'})    # 批量变更本地单据状态，变更状态为“C已审批”

    def Data_StockOut_Write_Back(self, **kwargs):
        """
        本接口用于实现直接调拨单 (STK_STKTRANSFERIN)  的审核功能
        :param kwargs:  替换para中参数，示例：   Numbers = []
        :return:
        """
        para = {"CreateOrgId": 0,
                "Numbers": [],
                "Ids": "",
                "SelectedPostId": 0,
                "NetworkCtrl": "",
                "IgnoreInterationFlag": "",
                "IsVerifyProcInst": "",
                }
        if kwargs:
            para.update(kwargs)
        response = api_sdk.Audit("STK_STKTRANSFERIN", para)
        res = json.loads(response)
        return res

    # =============== 回写生产领料单 ===============
    # =============== 回写生产领料单 ===============
    # =============== 回写生产领料单 ===============
    def Search_PRD_PickMtrl_Write_Back(self):
        """
        本接口用于查旬业务状态为“审核中”的数据，去驱动WMS去搬运；
        AGV搬运完成后，调用接口将单据状态变更为“C已审核”确认库存
        21 中裕软管科技股份有限公司  库表ID：101124
        23 安徽优耐德管道技术有限公司  库表ID：101127

        "and FDocumentStatus = 'B' " "and FCancelStatus = 'A' "

        search_data = stock_in_obj.search([
            # ('create_date', '>=', today.strftime('%Y-%m-%d 00:00:00')),
            # ('create_date', '<=', today.strftime('%Y-%m-%d 23:59:59')),
            ('SyncState', '=', 1),
            ('DocumentStatus', '=', 'B')
        ])
        :return:
        """
        stock_out_obj = self.env['wms.ship.order']  # 生产领料单
        # 查数据
        # today = datetime.date.today()
        _logger.info('生产领料单接口回写--当前时间：{}'.format(datetime.datetime.utcnow() + datetime.timedelta(hours=8)))
        search_data = stock_out_obj.search([('SyncState', '=', 1), ('DocumentStatus', '=', 'B')])
        check_values = []
        result = []
        _logger.info('生产领料单接口回写--传递数据：'.format(search_data))
        if len(search_data) == 0:
            return
        for line in search_data:
            check_values.append(line.TMBillNo)
        for value in sorted(list(set(check_values))):
            li = stock_out_obj.search([('TMBillNo', '=', value)])
            check_values1 = []
            for l in li:
                check_values1.append(l.SyncState)
            if len(list(set(check_values1))) == 1:
                result.append(l.TMBillNo)
            # 判断AGV是否执行完，搬运完成整单回写提交ERP生产领料单审核
        _logger.info('生产领料单接口回写--更新记录：'.format(sorted(list(set(result)))))
        self.Data_PRD_PickMtrl_Write_Back(Numbers=result)  # 批量提交云星空单据审批，变更状态为“C已审批”
        for tmp in result:
            c = stock_out_obj.search([('TMBillNo', '=', tmp)])
            c.write({'DocumentStatus': 'C'})  # 批量变更本地单据状态，变更状态为“C已审批”

    def Data_PRD_PickMtrl_Write_Back(self, **kwargs):
        """
        本接口用于实现生产领料单 (PRD_PickMtrl) 的单据查询(json)功能
        :param kwargs:  替换para中参数，示例：FieldKeys=“Fname",Limit=1000
        :return:
        """
        para = {"CreateOrgId": 0,
                "Numbers": [],
                "Ids": "",
                "SelectedPostId": 0,
                "NetworkCtrl": "",
                "IgnoreInterationFlag": "",
                "IsVerifyProcInst": "",
                }
        if kwargs:
            para.update(kwargs)
        response = api_sdk.Audit("PRD_PickMtrl", para)
        res = json.loads(response)
        return res
