-- 猫池短信系统数据库设计 (PostgreSQL)
-- 支持三层架构：总管理员 -> 渠道管理员 -> 渠道操作用户

-- 创建数据库
-- CREATE DATABASE sms_pool_system;

-- 使用数据库
-- \c sms_pool_system;

-- 创建序列和扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===============================
-- 1. 总管理员账号表
-- ===============================
CREATE TABLE super_admins (
    admins_id SERIAL PRIMARY KEY,
    admins_username VARCHAR(50) UNIQUE NOT NULL,
    admins_password_hash VARCHAR(255) NOT NULL,
    admins_realname VARCHAR(100),
    admins_email VARCHAR(100),
    admins_status VARCHAR(20) DEFAULT 'active',
    admins_permissions JSON,
    last_login_time TIMESTAMP,
    last_login_ip VARCHAR(50),
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 添加注释
COMMENT ON TABLE super_admins IS '总管理员账号表';
COMMENT ON COLUMN super_admins.admins_username IS '管理员用户名';
COMMENT ON COLUMN super_admins.admins_password_hash IS '密码哈希';
COMMENT ON COLUMN super_admins.admins_realname IS '真实姓名';
COMMENT ON COLUMN super_admins.admins_email IS '邮箱';
COMMENT ON COLUMN super_admins.admins_status IS '状态';
COMMENT ON COLUMN super_admins.admins_permissions IS '权限配置';
COMMENT ON COLUMN super_admins.last_login_time IS '最后登录时间';
COMMENT ON COLUMN super_admins.last_login_ip IS '最后登录IP';
COMMENT ON COLUMN super_admins.created_time IS '创建时间';
COMMENT ON COLUMN super_admins.updated_time IS '更新时间';

-- 创建索引
CREATE INDEX idx_super_admins_username ON super_admins(admins_username);

-- ===============================
-- 2. 渠道用户表（渠道管理员）
-- ===============================
CREATE TABLE channel_users (
    users_id SERIAL PRIMARY KEY,
    users_name VARCHAR(50) UNIQUE NOT NULL,
    users_password_hash VARCHAR(255) NOT NULL,
    users_real_name VARCHAR(100),
    users_total_credits BIGINT DEFAULT 0,
    users_used_credits BIGINT DEFAULT 0,
    users_available_credits BIGINT GENERATED ALWAYS AS (users_total_credits - users_used_credits) STORED,
    users_sms_rate DECIMAL(10,4) DEFAULT 1.0000,
    users_mms_rate DECIMAL(10,4) DEFAULT 3.0000,
    users_status VARCHAR(20) DEFAULT 'active',
    users_last_login_time TIMESTAMP,
    users_last_login_ip VARCHAR(50),
    created_by INTEGER REFERENCES super_admins(admins_id),
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_users_credits_positive CHECK (users_total_credits >= 0 AND users_used_credits >= 0)
);

-- 添加注释
COMMENT ON TABLE channel_users IS '渠道用户表（渠道管理员）';
COMMENT ON COLUMN channel_users.users_name IS '渠道用户名';
COMMENT ON COLUMN channel_users.users_password_hash IS '密码哈希';
COMMENT ON COLUMN channel_users.users_real_name IS '真实姓名';
COMMENT ON COLUMN channel_users.users_total_credits IS '总积分';
COMMENT ON COLUMN channel_users.users_used_credits IS '已使用积分';
COMMENT ON COLUMN channel_users.users_available_credits IS '可用积分';
COMMENT ON COLUMN channel_users.users_sms_rate IS '短信费率（每条消耗积分）';
COMMENT ON COLUMN channel_users.users_mms_rate IS '彩信费率（每条消耗积分）';
COMMENT ON COLUMN channel_users.users_status IS '状态：active-活跃，inactive-禁用，suspended-暂停';
COMMENT ON COLUMN channel_users.users_last_login_time IS '最后登录时间';
COMMENT ON COLUMN channel_users.users_last_login_ip IS '最后登录IP';
COMMENT ON COLUMN channel_users.created_by IS '创建人';
COMMENT ON COLUMN channel_users.created_time IS '创建时间';
COMMENT ON COLUMN channel_users.updated_time IS '更新时间';

-- 创建索引
CREATE INDEX idx_channel_users_username ON channel_users(users_name);
CREATE INDEX idx_channel_users_status ON channel_users(users_status);

-- ===============================
-- 3. 渠道操作用户表
-- ===============================
CREATE TABLE channel_operators (
    operators_id SERIAL PRIMARY KEY,
    operators_username VARCHAR(50) UNIQUE NOT NULL,
    operators_password_hash VARCHAR(255) NOT NULL,
    operators_real_name VARCHAR(100),
    channel_users_id INTEGER NOT NULL REFERENCES channel_users(users_id) ON DELETE CASCADE,
    operators_total_credits BIGINT DEFAULT 0,
    operators_used_credits BIGINT DEFAULT 0,
    operators_available_credits BIGINT GENERATED ALWAYS AS (operators_total_credits - operators_used_credits) STORED,
    operators_daily_limit BIGINT DEFAULT 0,
    operators_mac_address VARCHAR(20),
    operators_device_info JSON,
    operators_status VARCHAR(20) DEFAULT 'active',
    operators_last_login_time TIMESTAMP,
    operators_last_login_ip VARCHAR(50),
    created_by INTEGER REFERENCES channel_users(users_id),
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_operator_credits_positive CHECK (operators_total_credits >= 0 AND operators_used_credits >= 0)
);

-- 添加注释
COMMENT ON TABLE channel_operators IS '渠道操作用户表';
COMMENT ON COLUMN channel_operators.operators_username IS '操作用户名';
COMMENT ON COLUMN channel_operators.operators_password_hash IS '密码哈希';
COMMENT ON COLUMN channel_operators.operators_real_name IS '真实姓名';
COMMENT ON COLUMN channel_operators.channel_users_id IS '所属渠道用户ID';
COMMENT ON COLUMN channel_operators.operators_total_credits IS '总积分';
COMMENT ON COLUMN channel_operators.operators_used_credits IS '已使用积分';
COMMENT ON COLUMN channel_operators.operators_available_credits IS '可用积分';
COMMENT ON COLUMN channel_operators.operators_daily_limit IS '日发送限制';
COMMENT ON COLUMN channel_operators.operators_mac_address IS '绑定的MAC地址';
COMMENT ON COLUMN channel_operators.operators_device_info IS '设备信息';
COMMENT ON COLUMN channel_operators.operators_status IS '状态：active-活跃，inactive-禁用';
COMMENT ON COLUMN channel_operators.operators_last_login_time IS '最后登录时间';
COMMENT ON COLUMN channel_operators.operators_last_login_ip IS '最后登录IP';
COMMENT ON COLUMN channel_operators.created_by IS '创建人';
COMMENT ON COLUMN channel_operators.created_time IS '创建时间';
COMMENT ON COLUMN channel_operators.updated_time IS '更新时间';

-- 创建索引
CREATE INDEX idx_channel_operators_username ON channel_operators(operators_username);
CREATE INDEX idx_channel_operators_channel_user_id ON channel_operators(channel_users_id);
CREATE INDEX idx_channel_operators_status ON channel_operators(operators_status);
CREATE INDEX idx_channel_operators_mac ON channel_operators(operators_mac_address);

-- ===============================
-- 4. 渠道用户积分变动表
-- ===============================
CREATE TABLE channel_credit_logs (
    id SERIAL PRIMARY KEY,
    channel_users_id INTEGER NOT NULL REFERENCES channel_users(users_id) ON DELETE CASCADE,
    change_type VARCHAR(20) NOT NULL,
    change_amount BIGINT NOT NULL,
    before_balance BIGINT NOT NULL,
    after_balance BIGINT NOT NULL,
    operator_type VARCHAR(20),
    operator_id INTEGER,
    operator_name VARCHAR(100),
    description TEXT,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 添加注释
COMMENT ON TABLE channel_credit_logs IS '渠道用户积分变动表';
COMMENT ON COLUMN channel_credit_logs.channel_users_id IS '渠道用户ID';
COMMENT ON COLUMN channel_credit_logs.change_type IS '变动类型：recharge-充值，allocate-分配';
COMMENT ON COLUMN channel_credit_logs.change_amount IS '变动金额（正数为增加，负数为减少）';
COMMENT ON COLUMN channel_credit_logs.before_balance IS '变动前余额';
COMMENT ON COLUMN channel_credit_logs.after_balance IS '变动后余额';
COMMENT ON COLUMN channel_credit_logs.operator_type IS '操作者类型：super_admin-总管理员，channel_user-渠道用户';
COMMENT ON COLUMN channel_credit_logs.operator_id IS '操作者ID';
COMMENT ON COLUMN channel_credit_logs.operator_name IS '操作者姓名';
COMMENT ON COLUMN channel_credit_logs.description IS '变动描述';
COMMENT ON COLUMN channel_credit_logs.created_time IS '创建时间';

-- 创建索引
CREATE INDEX idx_channel_credit_logs_channel_user_id ON channel_credit_logs(channel_users_id);
CREATE INDEX idx_channel_credit_logs_change_type ON channel_credit_logs(change_type);
CREATE INDEX idx_channel_credit_logs_created_time ON channel_credit_logs(created_time);

-- ===============================
-- 5. 渠道操作用户积分变动表
-- ===============================
CREATE TABLE operator_credit_logs (
    id SERIAL PRIMARY KEY,
    operators_id INTEGER NOT NULL REFERENCES channel_operators(operators_id) ON DELETE CASCADE,
    channel_users_id INTEGER NOT NULL REFERENCES channel_users(users_id),
    change_type VARCHAR(20) NOT NULL,
    change_amount BIGINT NOT NULL,
    before_balance BIGINT NOT NULL,
    after_balance BIGINT NOT NULL,
    related_task_id INTEGER,
    related_message_id INTEGER,
    operator_type VARCHAR(20),
    operator_by INTEGER,
    operator_name VARCHAR(100),
    description TEXT,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 添加注释
COMMENT ON TABLE operator_credit_logs IS '渠道操作用户积分变动表';
COMMENT ON COLUMN operator_credit_logs.operators_id IS '操作用户ID';
COMMENT ON COLUMN operator_credit_logs.channel_users_id IS '所属渠道用户ID';
COMMENT ON COLUMN operator_credit_logs.change_type IS '变动类型：recharge-充值，consume-消费';
COMMENT ON COLUMN operator_credit_logs.change_amount IS '变动金额';
COMMENT ON COLUMN operator_credit_logs.before_balance IS '变动前余额';
COMMENT ON COLUMN operator_credit_logs.after_balance IS '变动后余额';
COMMENT ON COLUMN operator_credit_logs.related_task_id IS '关联任务ID';
COMMENT ON COLUMN operator_credit_logs.related_message_id IS '关联消息ID';
COMMENT ON COLUMN operator_credit_logs.operator_type IS '操作者类型：channel_user-渠道管理员，system-系统消费';
COMMENT ON COLUMN operator_credit_logs.operator_by IS '操作者ID';
COMMENT ON COLUMN operator_credit_logs.operator_name IS '操作者姓名';
COMMENT ON COLUMN operator_credit_logs.description IS '变动描述';
COMMENT ON COLUMN operator_credit_logs.created_time IS '创建时间';

-- 创建索引
CREATE INDEX idx_operator_credit_logs_operator_id ON operator_credit_logs(operators_id);
CREATE INDEX idx_operator_credit_logs_channel_user_id ON operator_credit_logs(channel_users_id);
CREATE INDEX idx_operator_credit_logs_change_type ON operator_credit_logs(change_type);
CREATE INDEX idx_operator_credit_logs_created_time ON operator_credit_logs(created_time);

-- ===============================
-- 6. 任务表
-- ===============================
CREATE TABLE tasks (
    tasks_id SERIAL PRIMARY KEY,
    tasks_uuid UUID DEFAULT uuid_generate_v4() UNIQUE,
    tasks_title VARCHAR(200) NOT NULL,
    tasks_mode VARCHAR(20) NOT NULL DEFAULT 'sms',
    tasks_subject_name VARCHAR(200),
    tasks_message_content TEXT NOT NULL,
    tasks_mms_attachments JSON,
    templates_id INTEGER,
    tasks_total_count INTEGER NOT NULL DEFAULT 0,
    tasks_success_count INTEGER DEFAULT 0,
    tasks_failed_count INTEGER DEFAULT 0,
    tasks_pending_count INTEGER DEFAULT 0,
    tasks_status VARCHAR(20) DEFAULT 'draft',
    tasks_priority INTEGER DEFAULT 5,
    tasks_schedule_type VARCHAR(20) DEFAULT 'immediate',
    tasks_scheduled_time TIMESTAMP,
    tasks_recurring_config JSON,
    tasks_send_config JSON,
    tasks_port_config JSON,
    tasks_rate_limit_config JSON,
    tasks_estimated_credits BIGINT,
    tasks_actual_credits BIGINT DEFAULT 0,
    operators_id INTEGER NOT NULL REFERENCES channel_operators(operators_id),
    channel_users_id INTEGER NOT NULL REFERENCES channel_users(users_id),
    tasks_started_time TIMESTAMP,
    tasks_completed_time TIMESTAMP,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 添加注释
COMMENT ON TABLE tasks IS '任务表';
COMMENT ON COLUMN tasks.tasks_uuid IS '任务唯一标识';
COMMENT ON COLUMN tasks.tasks_title IS '任务标题';
COMMENT ON COLUMN tasks.tasks_mode IS '任务模式：sms-短信，mms-彩信';
COMMENT ON COLUMN tasks.tasks_subject_name IS '主题名称（彩信专用）';
COMMENT ON COLUMN tasks.tasks_message_content IS '短信/彩信内容';
COMMENT ON COLUMN tasks.tasks_mms_attachments IS '彩信附件信息';
COMMENT ON COLUMN tasks.templates_id IS '消息模板ID';
COMMENT ON COLUMN tasks.tasks_total_count IS '总发送量';
COMMENT ON COLUMN tasks.tasks_success_count IS '成功数量';
COMMENT ON COLUMN tasks.tasks_failed_count IS '失败数量';
COMMENT ON COLUMN tasks.tasks_pending_count IS '待发送数量';
COMMENT ON COLUMN tasks.tasks_status IS '状态：draft-草稿，pending-待发送，running-发送中，paused-暂停，completed-完成，failed-失败，cancelled-取消';
COMMENT ON COLUMN tasks.tasks_priority IS '优先级：1-5，数字越小优先级越高';
COMMENT ON COLUMN tasks.tasks_schedule_type IS '调度类型：immediate-立即，scheduled-定时，recurring-循环';
COMMENT ON COLUMN tasks.tasks_scheduled_time IS '计划发送时间';
COMMENT ON COLUMN tasks.tasks_recurring_config IS '循环配置';
COMMENT ON COLUMN tasks.tasks_send_config IS '发送配置（间隔、重试等）';
COMMENT ON COLUMN tasks.tasks_port_config IS '端口配置';
COMMENT ON COLUMN tasks.tasks_rate_limit_config IS '频率限制配置';
COMMENT ON COLUMN tasks.tasks_estimated_credits IS '预估消耗积分';
COMMENT ON COLUMN tasks.tasks_actual_credits IS '实际消耗积分';
COMMENT ON COLUMN tasks.operators_id IS '创建的操作用户ID';
COMMENT ON COLUMN tasks.channel_users_id IS '所属渠道用户ID';
COMMENT ON COLUMN tasks.tasks_started_time IS '开始时间';
COMMENT ON COLUMN tasks.tasks_completed_time IS '完成时间';
COMMENT ON COLUMN tasks.created_time IS '创建时间';
COMMENT ON COLUMN tasks.updated_time IS '更新时间';

-- 创建索引
CREATE INDEX idx_tasks_operator_id ON tasks(operators_id);
CREATE INDEX idx_tasks_channel_user_id ON tasks(channel_users_id);
CREATE INDEX idx_tasks_status ON tasks(tasks_status);
CREATE INDEX idx_tasks_task_mode ON tasks(tasks_mode);
CREATE INDEX idx_tasks_created_time ON tasks(created_time);

-- ===============================
-- 7. 任务号码明细表
-- ===============================
CREATE TABLE task_message_details (
    details_id SERIAL PRIMARY KEY,
    tasks_id INTEGER NOT NULL REFERENCES tasks(tasks_id) ON DELETE CASCADE,
    recipient_number VARCHAR(20) NOT NULL,
    sender_number VARCHAR(20),
    details_sender_port VARCHAR(50),
    details_operator_name VARCHAR(50),
    details_status VARCHAR(20) DEFAULT 'pending',
    details_failure_reason VARCHAR(200),
    details_message_id VARCHAR(100),
    send_time TIMESTAMP,
    delivery_time TIMESTAMP,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    response_time INTEGER
);

-- 添加注释
COMMENT ON TABLE task_message_details IS '任务号码明细表';
COMMENT ON COLUMN task_message_details.tasks_id IS '任务ID';
COMMENT ON COLUMN task_message_details.recipient_number IS '接收号码';
COMMENT ON COLUMN task_message_details.sender_number IS '发送号码';
COMMENT ON COLUMN task_message_details.details_sender_port IS '发送串口';
COMMENT ON COLUMN task_message_details.details_operator_name IS '运营商：移动、联通、电信等';
COMMENT ON COLUMN task_message_details.details_status IS '发送状态：pending-待发送，sending-发送中，success-成功，failed-失败，timeout-超时';
COMMENT ON COLUMN task_message_details.details_failure_reason IS '失败原因';
COMMENT ON COLUMN task_message_details.details_message_id IS '运营商返回的消息ID';
COMMENT ON COLUMN task_message_details.send_time IS '发送时间';
COMMENT ON COLUMN task_message_details.delivery_time IS '接收时间（状态回执时间）';
COMMENT ON COLUMN task_message_details.created_time IS '创建时间';
COMMENT ON COLUMN task_message_details.updated_time IS '更新时间';
COMMENT ON COLUMN task_message_details.response_time IS '响应时间（毫秒）';

-- 创建索引
CREATE INDEX idx_task_message_details_task_id ON task_message_details(tasks_id);
CREATE INDEX idx_task_message_details_recipient_number ON task_message_details(recipient_number);
CREATE INDEX idx_task_message_details_send_status ON task_message_details(details_status);
CREATE INDEX idx_task_message_details_send_time ON task_message_details(send_time);

-- ===============================
-- 8. 扩展表建议
-- ===============================

-- 8.1 设备授权表
CREATE TABLE device_authorizations (
    id SERIAL PRIMARY KEY,
    mac_address VARCHAR(20) UNIQUE NOT NULL,
    device_name VARCHAR(100),
    device_type VARCHAR(50),
    system_info JSON,
    is_authorized BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'pending',
    register_ip VARCHAR(50),
    register_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_time TIMESTAMP
);

-- 添加注释
COMMENT ON TABLE device_authorizations IS '设备授权表';
COMMENT ON COLUMN device_authorizations.mac_address IS 'MAC地址';
COMMENT ON COLUMN device_authorizations.device_name IS '设备名称';
COMMENT ON COLUMN device_authorizations.device_type IS '设备类型';
COMMENT ON COLUMN device_authorizations.system_info IS '系统信息';
COMMENT ON COLUMN device_authorizations.is_authorized IS '是否授权';
COMMENT ON COLUMN device_authorizations.status IS '状态：pending-待授权，active-已授权，blocked-已封锁';
COMMENT ON COLUMN device_authorizations.register_ip IS '注册IP';
COMMENT ON COLUMN device_authorizations.register_time IS '注册时间';
COMMENT ON COLUMN device_authorizations.last_active_time IS '最后活跃时间';

-- 8.2 消息模板表
CREATE TABLE message_templates (
    templates_id SERIAL PRIMARY KEY,
    templates_name VARCHAR(200) NOT NULL,
    templates_type VARCHAR(20) DEFAULT 'sms',
    templates_content TEXT,
    templates_variables JSON,
    templates_config JSON,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 添加注释
COMMENT ON TABLE message_templates IS '消息模板表';
COMMENT ON COLUMN message_templates.templates_name IS '模板名称';
COMMENT ON COLUMN message_templates.templates_type IS '模板类型：sms、mms';
COMMENT ON COLUMN message_templates.templates_content IS '模板内容';
COMMENT ON COLUMN message_templates.templates_variables IS '模板变量';
COMMENT ON COLUMN message_templates.templates_config IS '模板配置';

-- 8.3 数据字典表
CREATE TABLE data_dictionaries (
    id SERIAL PRIMARY KEY,
    dict_type VARCHAR(50) NOT NULL,
    dict_code VARCHAR(50) NOT NULL,
    dict_label VARCHAR(200) NOT NULL,
    dict_value VARCHAR(500),
    description TEXT,
    created_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(dict_type, dict_code)
);

-- 添加注释
COMMENT ON TABLE data_dictionaries IS '数据字典表';
COMMENT ON COLUMN data_dictionaries.dict_type IS '字典类型';
COMMENT ON COLUMN data_dictionaries.dict_code IS '字典代码';
COMMENT ON COLUMN data_dictionaries.dict_label IS '字典标签';
COMMENT ON COLUMN data_dictionaries.dict_value IS '字典值';
COMMENT ON COLUMN data_dictionaries.description IS '描述';

-- 8.4 用户登录日志表
CREATE TABLE user_login_logs (
    id SERIAL PRIMARY KEY,
    user_type VARCHAR(20) NOT NULL,
    user_id INTEGER NOT NULL,
    username VARCHAR(50),
    login_ip VARCHAR(50),
    login_result VARCHAR(20) DEFAULT 'success',
    failure_reason VARCHAR(100),
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 添加注释
COMMENT ON TABLE user_login_logs IS '用户登录日志表';
COMMENT ON COLUMN user_login_logs.user_type IS '用户类型';
COMMENT ON COLUMN user_login_logs.user_id IS '用户ID';
COMMENT ON COLUMN user_login_logs.username IS '用户名称';
COMMENT ON COLUMN user_login_logs.login_ip IS '登陆IP';
COMMENT ON COLUMN user_login_logs.login_result IS '登陆状态success，failed';
COMMENT ON COLUMN user_login_logs.failure_reason IS '失败原因';

-- 创建索引
CREATE INDEX idx_user_login_logs_user ON user_login_logs(user_type, user_id);
CREATE INDEX idx_user_login_logs_time ON user_login_logs(login_time);
CREATE INDEX idx_user_login_logs_ip ON user_login_logs(login_ip);

-- ===============================
-- 初始化数据
-- ===============================

-- 插入默认超级管理员
INSERT INTO super_admins (admins_username, admins_password_hash, admins_realname, admins_email, admins_status) VALUES
('superadmin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdUHK4E6l8I8a', '超级管理员', 'admin@example.com', 'active');

-- 插入数据字典基础数据
INSERT INTO data_dictionaries (dict_type, dict_code, dict_label, dict_value, description) VALUES
-- 用户状态
('users_status', 'active', '活跃', 'active', '用户正常使用状态'),
('users_status', 'inactive', '非活跃', 'inactive', '用户暂时不使用'),
('users_status', 'suspended', '暂停', 'suspended', '用户被暂停使用'),
('users_status', 'blocked', '封锁', 'blocked', '用户被封锁'),

-- 任务状态
('tasks_status', 'draft', '草稿', 'draft', '任务草稿状态'),
('tasks_status', 'pending', '待发送', 'pending', '任务等待发送'),
('tasks_status', 'running', '发送中', 'running', '任务正在发送'),
('tasks_status', 'paused', '暂停', 'paused', '任务暂停'),
('tasks_status', 'completed', '完成', 'completed', '任务完成'),
('tasks_status', 'failed', '失败', 'failed', '任务失败'),
('tasks_status', 'cancelled', '取消', 'cancelled', '任务取消'),

-- 消息状态
('details_status', 'pending', '待发送', 'pending', '消息待发送'),
('details_status', 'sending', '发送中', 'sending', '消息发送中'),
('details_status', 'success', '成功', 'success', '消息发送成功'),
('details_status', 'failed', '失败', 'failed', '消息发送失败'),
('details_status', 'timeout', '超时', 'timeout', '消息发送超时'),

-- 消息类型
('tasks_mode', 'sms', '短信', 'sms', '普通短信'),
('tasks_mode', 'mms', '彩信', 'mms', '多媒体信息');

-- ===============================
-- 创建存储过程/函数
-- ===============================

-- 充值积分的存储过程
CREATE OR REPLACE FUNCTION recharge_channel_credits(
    p_channel_user_id INTEGER,
    p_amount BIGINT,
    p_operator_type VARCHAR(20),
    p_operator_id INTEGER,
    p_operator_name VARCHAR(100),
    p_description TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_before_balance BIGINT;
    v_after_balance BIGINT;
BEGIN
    -- 获取当前余额
    SELECT users_available_credits INTO v_before_balance
    FROM channel_users
    WHERE users_id = p_channel_user_id;

    IF v_before_balance IS NULL THEN
        RAISE EXCEPTION '渠道用户不存在';
    END IF;

    -- 更新余额
    UPDATE channel_users
    SET users_total_credits = users_total_credits + p_amount,
        updated_time = CURRENT_TIMESTAMP
    WHERE users_id = p_channel_user_id;

    -- 获取更新后余额
    SELECT users_available_credits INTO v_after_balance
    FROM channel_users
    WHERE users_id = p_channel_user_id;

    -- 记录积分变动日志
    INSERT INTO channel_credit_logs (
        channel_users_id, change_type, change_amount,
        before_balance, after_balance, operator_type,
        operator_id, operator_name, description
    ) VALUES (
        p_channel_user_id, 'recharge', p_amount,
        v_before_balance, v_after_balance, p_operator_type,
        p_operator_id, p_operator_name, p_description
    );

    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- 分配积分给操作用户的存储过程
CREATE OR REPLACE FUNCTION allocate_operator_credits(
    p_operator_id INTEGER,
    p_amount BIGINT,
    p_channel_user_id INTEGER,
    p_operator_name VARCHAR(100),
    p_description TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_channel_available BIGINT;
    v_operator_before BIGINT;
    v_operator_after BIGINT;
    v_channel_before BIGINT;
    v_channel_after BIGINT;
BEGIN
    -- 检查渠道用户余额
    SELECT users_available_credits INTO v_channel_available
    FROM channel_users
    WHERE users_id = p_channel_user_id;

    IF v_channel_available < p_amount THEN
        RAISE EXCEPTION '渠道用户积分余额不足';
    END IF;

    -- 获取操作用户当前余额
    SELECT operators_available_credits INTO v_operator_before
    FROM channel_operators
    WHERE operators_id = p_operator_id;

    -- 获取渠道用户当前余额
    SELECT users_available_credits INTO v_channel_before
    FROM channel_users
    WHERE users_id = p_channel_user_id;

    -- 更新渠道用户余额（减少）
    UPDATE channel_users
    SET users_used_credits = users_used_credits + p_amount,
        updated_time = CURRENT_TIMESTAMP
    WHERE users_id = p_channel_user_id;

    -- 更新操作用户余额（增加）
    UPDATE channel_operators
    SET operators_total_credits = operators_total_credits + p_amount,
        updated_time = CURRENT_TIMESTAMP
    WHERE operators_id = p_operator_id;

    -- 获取更新后余额
    SELECT operators_available_credits INTO v_operator_after
    FROM channel_operators
    WHERE operators_id = p_operator_id;

    SELECT users_available_credits INTO v_channel_after
    FROM channel_users
    WHERE users_id = p_channel_user_id;

    -- 记录渠道用户积分变动日志
    INSERT INTO channel_credit_logs (
        channel_users_id, change_type, change_amount,
        before_balance, after_balance, operator_type,
        operator_id, operator_name, description
    ) VALUES (
        p_channel_user_id, 'allocate', -p_amount,
        v_channel_before, v_channel_after, 'channel_user',
        p_channel_user_id, p_operator_name, p_description
    );

    -- 记录操作用户积分变动日志
    INSERT INTO operator_credit_logs (
        operators_id, channel_users_id, change_type, change_amount,
        before_balance, after_balance, operator_type,
        operator_by, operator_name, description
    ) VALUES (
        p_operator_id, p_channel_user_id, 'recharge', p_amount,
        v_operator_before, v_operator_after, 'channel_user',
        p_channel_user_id, p_operator_name, p_description
    );

    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- 消费积分的存储过程
CREATE OR REPLACE FUNCTION consume_operator_credits(
    p_operator_id INTEGER,
    p_amount BIGINT,
    p_task_id INTEGER DEFAULT NULL,
    p_description TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    v_available_credits BIGINT;
    v_before_balance BIGINT;
    v_after_balance BIGINT;
    v_channel_user_id INTEGER;
BEGIN
    -- 获取当前余额和渠道用户ID
    SELECT operators_available_credits, channel_users_id
    INTO v_available_credits, v_channel_user_id
    FROM channel_operators
    WHERE operators_id = p_operator_id;

    IF v_available_credits < p_amount THEN
        RAISE EXCEPTION '操作用户积分余额不足';
    END IF;

    v_before_balance := v_available_credits;

    -- 更新余额
    UPDATE channel_operators
    SET operators_used_credits = operators_used_credits + p_amount,
        updated_time = CURRENT_TIMESTAMP
    WHERE operators_id = p_operator_id;

    -- 获取更新后余额
    SELECT operators_available_credits INTO v_after_balance
    FROM channel_operators
    WHERE operators_id = p_operator_id;

    -- 记录积分变动日志
    INSERT INTO operator_credit_logs (
        operators_id, channel_users_id, change_type, change_amount,
        before_balance, after_balance, related_task_id,
        operator_type, description
    ) VALUES (
        p_operator_id, v_channel_user_id, 'consume', -p_amount,
        v_before_balance, v_after_balance, p_task_id,
        'system', p_description
    );

    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        RETURN FALSE;
END;
$$ LANGUAGE plpgsql;

-- ===============================
-- 示例数据插入（用于测试）
-- ===============================

-- 插入示例渠道用户
INSERT INTO channel_users (
    users_name, users_password_hash, users_real_name,
    users_total_credits, users_sms_rate, users_mms_rate, created_by
) VALUES
('channel001', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdUHK4E6l8I8a', '测试渠道用户', 10000, 1.0000, 3.0000, 1);

-- 插入示例操作用户
INSERT INTO channel_operators (
    operators_username, operators_password_hash, operators_real_name,
    channel_users_id, operators_total_credits, operators_daily_limit, created_by
) VALUES
('operator001', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBdUHK4E6l8I8a', '测试操作员', 1, 1000, 5000, 1);

-- 插入示例消息模板
INSERT INTO message_templates (templates_name, templates_type, templates_content, templates_variables) VALUES
('验证码模板', 'sms', '您的验证码是：{code}，请在5分钟内使用。', '["code"]'),
('通知模板', 'sms', '亲爱的{name}，您有一条新消息：{message}', '["name", "message"]'),
('彩信模板', 'mms', '欢迎使用我们的服务！', '[]');

-- ===============================
-- 创建更新时间触发器
-- ===============================

-- 创建通用的更新时间函数
CREATE OR REPLACE FUNCTION update_updated_time_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_time = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为各表创建更新时间触发器
CREATE TRIGGER trigger_super_admins_updated_time
    BEFORE UPDATE ON super_admins
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_time_column();

CREATE TRIGGER trigger_channel_users_updated_time
    BEFORE UPDATE ON channel_users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_time_column();

CREATE TRIGGER trigger_channel_operators_updated_time
    BEFORE UPDATE ON channel_operators
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_time_column();

CREATE TRIGGER trigger_tasks_updated_time
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_time_column();

CREATE TRIGGER trigger_task_message_details_updated_time
    BEFORE UPDATE ON task_message_details
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_time_column();

CREATE TRIGGER trigger_message_templates_updated_time
    BEFORE UPDATE ON message_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_time_column();

CREATE TRIGGER trigger_data_dictionaries_updated_time
    BEFORE UPDATE ON data_dictionaries
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_time_column();