import React, { useState } from 'react';
import { Card, Form, Input, Button, message } from 'antd';
import ipProxyAPI from '@/utils/ipProxyAPI';

const SettingsPage: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleUpdatePassword = async (values: any) => {
    try {
      if (values.newPassword !== values.confirmPassword) {
        message.error('两次输入的密码不一致');
        return;
      }
      
      setLoading(true);
      await ipProxyAPI.updateAdminPassword(values.oldPassword, values.newPassword);
      message.success('密码修改成功');
      form.resetFields();
    } catch (error) {
      console.error('修改密码失败:', error);
      message.error('修改密码失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className="p-6">
        <Card title="修改管理员密码" style={{ maxWidth: 500 }}>
          <Form
            form={form}
            layout="vertical"
            onFinish={handleUpdatePassword}
          >
            <Form.Item
              name="oldPassword"
              label="当前密码"
              rules={[{ required: true, message: '请输入当前密码' }]}
            >
              <Input.Password placeholder="请输入当前密码" />
            </Form.Item>

            <Form.Item
              name="newPassword"
              label="新密码"
              rules={[
                { required: true, message: '请输入新密码' },
                { min: 6, message: '密码长度不能小于6位' }
              ]}
            >
              <Input.Password placeholder="请输入新密码" />
            </Form.Item>

            <Form.Item
              name="confirmPassword"
              label="确认新密码"
              rules={[{ required: true, message: '请再次输入新密码' }]}
            >
              <Input.Password placeholder="请再次输入新密码" />
            </Form.Item>

            <Form.Item>
              <Button type="primary" htmlType="submit" loading={loading}>
                修改密码
              </Button>
            </Form.Item>
          </Form>
        </Card>
      </div>
    </>
  );
};

export default SettingsPage;