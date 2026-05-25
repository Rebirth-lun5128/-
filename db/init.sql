-- 外卖平台数据库初始化脚本
-- Database: food_delivery

CREATE DATABASE IF NOT EXISTS food_delivery DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE food_delivery;

-- ============================================================
-- 区域管理
-- ============================================================
CREATE TABLE regions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL COMMENT '区域名称',
    parent_id INT DEFAULT NULL COMMENT '上级区域',
    manager_id INT DEFAULT NULL COMMENT '区域管理者ID',
    sort_order INT DEFAULT 0,
    status TINYINT DEFAULT 1 COMMENT '1=启用 0=禁用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES regions(id) ON DELETE SET NULL
) ENGINE=InnoDB COMMENT='区域表';

-- ============================================================
-- 用户系统 (统一用户表，通过role区分)
-- ============================================================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    openid VARCHAR(100) UNIQUE COMMENT '微信openid',
    unionid VARCHAR(100) DEFAULT '' COMMENT '微信unionid',
    nickname VARCHAR(100) DEFAULT '' COMMENT '昵称',
    avatar VARCHAR(500) DEFAULT '' COMMENT '头像',
    phone VARCHAR(20) DEFAULT '' COMMENT '手机号',
    role ENUM('user', 'merchant', 'rider', 'region_admin', 'super_admin') NOT NULL DEFAULT 'user',
    region_id INT DEFAULT NULL COMMENT '所属区域',
    status TINYINT DEFAULT 1 COMMENT '1=正常 0=禁用',
    last_login DATETIME DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_openid (openid),
    INDEX idx_role (role),
    INDEX idx_region (region_id)
) ENGINE=InnoDB COMMENT='用户表';

-- ============================================================
-- 用户地址
-- ============================================================
CREATE TABLE user_addresses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    contact_name VARCHAR(50) NOT NULL COMMENT '联系人',
    contact_phone VARCHAR(20) NOT NULL COMMENT '联系电话',
    gender TINYINT DEFAULT 1 COMMENT '1=先生 2=女士',
    province VARCHAR(50) DEFAULT '',
    city VARCHAR(50) DEFAULT '',
    district VARCHAR(50) DEFAULT '',
    detail VARCHAR(200) NOT NULL COMMENT '详细地址',
    lat DECIMAL(10,7) DEFAULT NULL COMMENT '纬度',
    lng DECIMAL(10,7) DEFAULT NULL COMMENT '经度',
    label VARCHAR(50) DEFAULT '' COMMENT '标签(家/公司/学校)',
    is_default TINYINT DEFAULT 0 COMMENT '是否默认',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user (user_id)
) ENGINE=InnoDB COMMENT='用户地址表';

-- ============================================================
-- 商家/餐厅
-- ============================================================
CREATE TABLE restaurants (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '关联的商家用户ID',
    name VARCHAR(100) NOT NULL COMMENT '餐厅名称',
    logo VARCHAR(500) DEFAULT '' COMMENT 'Logo',
    banner VARCHAR(500) DEFAULT '' COMMENT '横幅',
    phone VARCHAR(20) DEFAULT '' COMMENT '联系电话',
    address VARCHAR(300) DEFAULT '' COMMENT '地址',
    lat DECIMAL(10,7) DEFAULT NULL,
    lng DECIMAL(10,7) DEFAULT NULL,
    category VARCHAR(50) DEFAULT '' COMMENT '分类(中餐/西餐/快餐等)',
    rating DECIMAL(2,1) DEFAULT 5.0 COMMENT '评分',
    monthly_sales INT DEFAULT 0 COMMENT '月销量',
    min_price DECIMAL(10,2) DEFAULT 0 COMMENT '起送价',
    delivery_fee DECIMAL(10,2) DEFAULT 0 COMMENT '配送费',
    delivery_time VARCHAR(20) DEFAULT '30分钟' COMMENT '预计配送时间',
    business_hours JSON DEFAULT NULL COMMENT '营业时间',
    notice VARCHAR(200) DEFAULT '' COMMENT '公告',
    status ENUM('open', 'closed', 'resting') DEFAULT 'closed' COMMENT '营业状态',
    verify_status ENUM('unverified', 'verified', 'rejected') DEFAULT 'unverified' COMMENT '平台核验状态(无需营业执照)',
    verify_method VARCHAR(50) DEFAULT '' COMMENT '核验方式: 现场核验/视频核验',
    verify_note VARCHAR(300) DEFAULT '' COMMENT '核验备注',
    stall_location VARCHAR(300) DEFAULT '' COMMENT '夜市摊位位置描述',
    id_card_photo VARCHAR(500) DEFAULT '' COMMENT '身份证照片(选填)',
    stall_photo VARCHAR(500) DEFAULT '' COMMENT '摊位照片(选填)',
    region_id INT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_region (region_id),
    INDEX idx_category (category),
    INDEX idx_status (status)
) ENGINE=InnoDB COMMENT='餐厅表';

-- ============================================================
-- 菜单分类
-- ============================================================
CREATE TABLE menu_categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    restaurant_id INT NOT NULL,
    name VARCHAR(50) NOT NULL COMMENT '分类名(热销/主食/饮品等)',
    sort_order INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
    INDEX idx_restaurant (restaurant_id)
) ENGINE=InnoDB COMMENT='菜单分类表';

-- ============================================================
-- 菜品
-- ============================================================
CREATE TABLE menu_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    restaurant_id INT NOT NULL,
    category_id INT DEFAULT NULL,
    name VARCHAR(100) NOT NULL COMMENT '菜品名称',
    image VARCHAR(500) DEFAULT '' COMMENT '图片',
    price DECIMAL(10,2) NOT NULL COMMENT '价格',
    original_price DECIMAL(10,2) DEFAULT NULL COMMENT '原价',
    description VARCHAR(300) DEFAULT '' COMMENT '描述',
    monthly_sales INT DEFAULT 0 COMMENT '月销量',
    is_recommended TINYINT DEFAULT 0 COMMENT '是否推荐',
    status TINYINT DEFAULT 1 COMMENT '1=上架 0=下架',
    sort_order INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES menu_categories(id) ON DELETE SET NULL,
    INDEX idx_restaurant (restaurant_id),
    INDEX idx_category (category_id)
) ENGINE=InnoDB COMMENT='菜品表';

-- ============================================================
-- 骑手信息
-- ============================================================
CREATE TABLE riders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '关联的用户ID',
    real_name VARCHAR(50) NOT NULL COMMENT '真实姓名',
    id_card VARCHAR(20) DEFAULT '' COMMENT '身份证号',
    phone VARCHAR(20) NOT NULL COMMENT '手机号',
    status ENUM('offline', 'online', 'busy') DEFAULT 'offline' COMMENT '骑手状态',
    lat DECIMAL(10,7) DEFAULT NULL COMMENT '当前位置纬度',
    lng DECIMAL(10,7) DEFAULT NULL COMMENT '当前位置经度',
    balance DECIMAL(10,2) DEFAULT 0 COMMENT '账户余额',
    total_orders INT DEFAULT 0 COMMENT '累计配送单数',
    rating DECIMAL(2,1) DEFAULT 5.0 COMMENT '骑手评分',
    audit_status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    region_id INT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_region (region_id),
    INDEX idx_status (status)
) ENGINE=InnoDB COMMENT='骑手表';

-- ============================================================
-- 订单
-- ============================================================
CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_no VARCHAR(30) NOT NULL UNIQUE COMMENT '订单编号',
    user_id INT NOT NULL COMMENT '下单用户',
    restaurant_id INT NOT NULL COMMENT '餐厅',
    rider_id INT DEFAULT NULL COMMENT '接单骑手',
    address_snapshot JSON NOT NULL COMMENT '收货地址快照',
    items_total DECIMAL(10,2) NOT NULL COMMENT '菜品总价',
    delivery_fee DECIMAL(10,2) DEFAULT 0 COMMENT '配送费',
    package_fee DECIMAL(10,2) DEFAULT 0 COMMENT '包装费',
    discount_amount DECIMAL(10,2) DEFAULT 0 COMMENT '优惠金额',
    total_price DECIMAL(10,2) NOT NULL COMMENT '实付金额',
    status ENUM('pending_pay','pending_accept','preparing','ready','delivering','delivered','completed','cancelled') NOT NULL DEFAULT 'pending_pay',
    cancel_reason VARCHAR(300) DEFAULT '' COMMENT '取消原因',
    cancel_by VARCHAR(20) DEFAULT '' COMMENT '取消方(user/merchant/rider/admin)',
    remark VARCHAR(200) DEFAULT '' COMMENT '备注',
    paid_at DATETIME DEFAULT NULL COMMENT '支付时间',
    accepted_at DATETIME DEFAULT NULL COMMENT '商家接单时间',
    ready_at DATETIME DEFAULT NULL COMMENT '出餐时间',
    picked_at DATETIME DEFAULT NULL COMMENT '骑手取餐时间',
    delivered_at DATETIME DEFAULT NULL COMMENT '送达时间',
    completed_at DATETIME DEFAULT NULL COMMENT '完成时间',
    region_id INT DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (restaurant_id) REFERENCES restaurants(id),
    FOREIGN KEY (rider_id) REFERENCES riders(id),
    INDEX idx_user (user_id),
    INDEX idx_restaurant (restaurant_id),
    INDEX idx_rider (rider_id),
    INDEX idx_status (status),
    INDEX idx_region (region_id),
    INDEX idx_created (created_at)
) ENGINE=InnoDB COMMENT='订单表';

-- ============================================================
-- 订单明细
-- ============================================================
CREATE TABLE order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    menu_item_id INT DEFAULT NULL,
    name VARCHAR(100) NOT NULL COMMENT '菜品名(快照)',
    image VARCHAR(500) DEFAULT '' COMMENT '图片(快照)',
    price DECIMAL(10,2) NOT NULL COMMENT '单价(快照)',
    quantity INT NOT NULL DEFAULT 1 COMMENT '数量',
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    INDEX idx_order (order_id)
) ENGINE=InnoDB COMMENT='订单明细表';

-- ============================================================
-- 订单时间线
-- ============================================================
CREATE TABLE order_timeline (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    status VARCHAR(30) NOT NULL COMMENT '状态',
    description VARCHAR(200) DEFAULT '' COMMENT '描述',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
    INDEX idx_order (order_id)
) ENGINE=InnoDB COMMENT='订单时间线';

-- ============================================================
-- 结算记录
-- ============================================================
CREATE TABLE settlements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    target_type ENUM('restaurant', 'rider') NOT NULL,
    target_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL COMMENT '结算金额',
    fee DECIMAL(10,2) DEFAULT 0 COMMENT '平台抽成',
    net_amount DECIMAL(10,2) NOT NULL COMMENT '实际到账',
    period VARCHAR(20) DEFAULT '' COMMENT '结算周期',
    status ENUM('pending', 'paid') DEFAULT 'pending',
    paid_at DATETIME DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_target (target_type, target_id)
) ENGINE=InnoDB COMMENT='结算表';

-- ============================================================
-- 系统配置
-- ============================================================
CREATE TABLE system_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    config_key VARCHAR(50) NOT NULL UNIQUE,
    config_value TEXT NOT NULL,
    description VARCHAR(200) DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='系统配置表';

-- ============================================================
-- 初始化默认数据
-- ============================================================

-- 区域数据
INSERT INTO regions (id, name, parent_id) VALUES
(1, '全城', NULL),
(2, '朝阳区', 1),
(3, '海淀区', 1),
(4, '西城区', 1),
(5, '东城区', 1);

-- 系统配置
INSERT INTO system_configs (config_key, config_value, description) VALUES
('platform_fee_rate', '0.15', '平台抽成比例'),
('delivery_fee_default', '5', '默认配送费(元)'),
('auto_cancel_minutes', '30', '未支付订单自动取消时间(分钟)'),
('rider_nearby_radius', '5', '骑手附近订单搜索半径(公里)');
