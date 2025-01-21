import React from 'react';
import { Form, Input, Button, Card, message } from 'antd';
import { LockOutlined } from '@ant-design/icons';
import styles from './index.module.less';

interface ChangePasswordForm {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

const SettingsPage: React.FC = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = React.useState(false);

  const handleSubmit = async (values: ChangePasswordForm) => {
    if (values.newPassword !== values.confirmPassword) {
      message.error('两次输入的新密码不一致');
      return;
    }

    setLoading(true);
    try {
      // TODO: 替换为实际的API调用
      await fetch('/api/user/change-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          oldPassword: values.currentPassword,
          newPassword: values.newPassword,
        }),
      });
      
      message.success('密码修改成功');
      form.resetFields();
    } catch (error) {
      message.error('密码修改失败');
    }
    setLoading(false);
  };

  return (
    <div className={styles.settings}>
      <Card
        title="修改管理员密码"
        bordered={false}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          className={styles.settingsForm}
        >
          <Form.Item
            name="currentPassword"
            label="当前密码"
            rules={[
              { required: true, message: '请输入当前密码' }
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请输入当前密码"
            />
          </Form.Item>

          <Form.Item
            name="newPassword"
            label="新密码"
            rules={[
              { required: true, message: '请输入新密码' }
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请输入新密码"
            />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            label="确认新密码"
            rules={[
              { required: true, message: '请再次输入新密码' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('newPassword') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('两次输入的密码不一致'));
                },
              }),
            ]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="请再次输入新密码"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
            >
              修改密码
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};

export default SettingsPage;