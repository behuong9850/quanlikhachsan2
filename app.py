import streamlit as st
st.image("IMG_malibu1234.jpg")
import mysql.connector
from mysql.connector import Error, IntegrityError
from datetime import datetime, date
import pandas as pd

# ============================================================
# CẤU HÌNH STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Hotel Manager",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# MYSQL AIVEN
# ============================================================

DB_USER = "avnadmin"
DB_PASSWORD = "AVNS_TX2oBXmTGGjXba6p7j1"
DB_HOST = "mysql-3a5ef2bc-binhquytoc.a.aivencloud.com"
DB_PORT = 14483
DB_NAME = "hotel_management"

DB_SSL_CONFIG = {
    "ssl_disabled": False,
    "ssl_verify_cert": False,
    "ssl_verify_identity": False,
}


# ============================================================
# KẾT NỐI DATABASE
# ============================================================

def get_connection():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connection_timeout=15,
            autocommit=False,
            **DB_SSL_CONFIG
        )

        if connection.is_connected():
            return connection

    except Error as e:
        st.error(f"Không thể kết nối MySQL: {e}")

    return None


# ============================================================
# KHỞI TẠO DATABASE
# ============================================================

def init_database():

    connection = get_connection()

    if not connection:
        return False

    cursor = None

    try:
        cursor = connection.cursor()

        # ----------------------------------------------------
        # BẢNG ROOMS
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rooms (
                id INT AUTO_INCREMENT PRIMARY KEY,
                room_number VARCHAR(20) NOT NULL UNIQUE,
                room_type VARCHAR(100) NOT NULL,
                price DECIMAL(15,2) NOT NULL DEFAULT 0,
                status VARCHAR(50) NOT NULL DEFAULT 'Trống',
                floor INT DEFAULT 1,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
            DEFAULT CHARSET=utf8mb4
            COLLATE=utf8mb4_unicode_ci
        """)

        # ----------------------------------------------------
        # BẢNG GUESTS
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS guests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(255) NOT NULL,
                id_number VARCHAR(100),
                phone VARCHAR(50),
                email VARCHAR(255),
                address TEXT,
                nationality VARCHAR(100),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY unique_id_number (id_number)
            ) ENGINE=InnoDB
            DEFAULT CHARSET=utf8mb4
            COLLATE=utf8mb4_unicode_ci
        """)

        # ----------------------------------------------------
        # BẢNG BOOKINGS
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                guest_id INT NOT NULL,
                room_id INT NOT NULL,
                check_in DATE NOT NULL,
                check_out DATE NOT NULL,
                adults INT DEFAULT 1,
                children INT DEFAULT 0,
                booking_status VARCHAR(50) DEFAULT 'Đã đặt',
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

                CONSTRAINT fk_booking_guest
                    FOREIGN KEY (guest_id)
                    REFERENCES guests(id)
                    ON DELETE CASCADE,

                CONSTRAINT fk_booking_room
                    FOREIGN KEY (room_id)
                    REFERENCES rooms(id)
                    ON DELETE RESTRICT
            ) ENGINE=InnoDB
            DEFAULT CHARSET=utf8mb4
            COLLATE=utf8mb4_unicode_ci
        """)

        # ----------------------------------------------------
        # BẢNG PAYMENTS
        # ----------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                booking_id INT NOT NULL,
                amount DECIMAL(15,2) NOT NULL DEFAULT 0,
                payment_method VARCHAR(100) DEFAULT 'Tiền mặt',
                payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,

                CONSTRAINT fk_payment_booking
                    FOREIGN KEY (booking_id)
                    REFERENCES bookings(id)
                    ON DELETE CASCADE
            ) ENGINE=InnoDB
            DEFAULT CHARSET=utf8mb4
            COLLATE=utf8mb4_unicode_ci
        """)

        connection.commit()

        # ----------------------------------------------------
        # TẠO DỮ LIỆU PHÒNG MẪU NẾU CHƯA CÓ
        # ----------------------------------------------------

        cursor.execute("SELECT COUNT(*) FROM rooms")
        room_count = cursor.fetchone()[0]

        if room_count == 0:

            sample_rooms = [
                ("101", "Standard", 800000, "Trống", 1),
                ("102", "Standard", 800000, "Trống", 1),
                ("103", "Deluxe", 1200000, "Trống", 1),
                ("104", "Deluxe", 1200000, "Trống", 1),
                ("201", "Standard", 800000, "Trống", 2),
                ("202", "Standard", 800000, "Trống", 2),
                ("203", "Deluxe", 1200000, "Trống", 2),
                ("204", "Deluxe", 1200000, "Trống", 2),
                ("301", "Suite", 2000000, "Trống", 3),
                ("302", "Suite", 2000000, "Trống", 3),
                ("303", "VIP", 3000000, "Trống", 3),
                ("304", "VIP", 3000000, "Trống", 3),
            ]

            cursor.executemany("""
                INSERT INTO rooms
                (
                    room_number,
                    room_type,
                    price,
                    status,
                    floor
                )
                VALUES (%s, %s, %s, %s, %s)
            """, sample_rooms)

            connection.commit()

        return True

    except Error as e:

        connection.rollback()
        st.error(f"Lỗi khởi tạo database: {e}")
        return False

    finally:

        if cursor:
            cursor.close()

        connection.close()


# ============================================================
# HÀM FORMAT TIỀN
# ============================================================

def format_money(value):

    if value is None:
        return "0 ₫"

    try:
        return f"{float(value):,.0f} ₫"
    except:
        return "0 ₫"


# ============================================================
# LẤY DỮ LIỆU
# ============================================================

def get_rooms():

    connection = get_connection()

    if not connection:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                id,
                room_number,
                room_type,
                price,
                status,
                floor,
                description,
                created_at
            FROM rooms
            ORDER BY CAST(room_number AS UNSIGNED)
        """

        return pd.read_sql(query, connection)

    except Exception as e:

        st.error(f"Lỗi lấy danh sách phòng: {e}")
        return pd.DataFrame()

    finally:
        connection.close()


def get_guests():

    connection = get_connection()

    if not connection:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                id,
                full_name,
                id_number,
                phone,
                email,
                address,
                nationality,
                created_at
            FROM guests
            ORDER BY id DESC
        """

        return pd.read_sql(query, connection)

    except Exception as e:

        st.error(f"Lỗi lấy khách hàng: {e}")
        return pd.DataFrame()

    finally:
        connection.close()


def get_bookings():

    connection = get_connection()

    if not connection:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                b.id,
                g.full_name,
                g.phone,
                g.id_number,
                r.room_number,
                r.room_type,
                r.price,
                b.check_in,
                b.check_out,
                b.adults,
                b.children,
                b.booking_status,
                b.notes,
                b.created_at
            FROM bookings b
            JOIN guests g ON b.guest_id = g.id
            JOIN rooms r ON b.room_id = r.id
            ORDER BY b.id DESC
        """

        return pd.read_sql(query, connection)

    except Exception as e:

        st.error(f"Lỗi lấy danh sách đặt phòng: {e}")
        return pd.DataFrame()

    finally:
        connection.close()


def get_payments():

    connection = get_connection()

    if not connection:
        return pd.DataFrame()

    try:

        query = """
            SELECT
                p.id,
                p.booking_id,
                g.full_name,
                r.room_number,
                p.amount,
                p.payment_method,
                p.payment_date,
                p.notes
            FROM payments p
            JOIN bookings b ON p.booking_id = b.id
            JOIN guests g ON b.guest_id = g.id
            JOIN rooms r ON b.room_id = r.id
            ORDER BY p.id DESC
        """

        return pd.read_sql(query, connection)

    except Exception as e:

        st.error(f"Lỗi lấy thanh toán: {e}")
        return pd.DataFrame()

    finally:
        connection.close()


# ============================================================
# THÊM PHÒNG
# ============================================================

def add_room(
    room_number,
    room_type,
    price,
    floor,
    description
):

    connection = get_connection()

    if not connection:
        return False

    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO rooms
            (
                room_number,
                room_type,
                price,
                status,
                floor,
                description
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            room_number,
            room_type,
            price,
            "Trống",
            floor,
            description
        ))

        connection.commit()

        return True

    except IntegrityError:

        connection.rollback()
        st.error("Số phòng đã tồn tại.")

        return False

    except Error as e:

        connection.rollback()
        st.error(f"Lỗi thêm phòng: {e}")

        return False

    finally:

        cursor.close()
        connection.close()


# ============================================================
# CẬP NHẬT PHÒNG
# ============================================================

def update_room(
    room_id,
    room_number,
    room_type,
    price,
    status,
    floor,
    description
):

    connection = get_connection()

    if not connection:
        return False

    cursor = connection.cursor()

    try:

        cursor.execute("""
            UPDATE rooms
            SET
                room_number = %s,
                room_type = %s,
                price = %s,
                status = %s,
                floor = %s,
                description = %s
            WHERE id = %s
        """, (
            room_number,
            room_type,
            price,
            status,
            floor,
            description,
            room_id
        ))

        connection.commit()

        return True

    except IntegrityError:

        connection.rollback()
        st.error("Số phòng đã tồn tại.")

        return False

    except Error as e:

        connection.rollback()
        st.error(f"Lỗi cập nhật phòng: {e}")

        return False

    finally:

        cursor.close()
        connection.close()


# ============================================================
# XÓA PHÒNG
# ============================================================

def delete_room(room_id):

    connection = get_connection()

    if not connection:
        return False

    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT COUNT(*)
            FROM bookings
            WHERE room_id = %s
        """, (room_id,))

        booking_count = cursor.fetchone()[0]

        if booking_count > 0:

            st.error(
                "Không thể xóa phòng vì phòng đã có lịch đặt."
            )

            return False

        cursor.execute("""
            DELETE FROM rooms
            WHERE id = %s
        """, (room_id,))

        connection.commit()

        return True

    except Error as e:

        connection.rollback()
        st.error(f"Lỗi xóa phòng: {e}")

        return False

    finally:

        cursor.close()
        connection.close()


# ============================================================
# TÌM HOẶC TẠO KHÁCH HÀNG
# ============================================================

def get_or_create_guest(
    full_name,
    id_number,
    phone,
    email,
    address,
    nationality
):

    connection = get_connection()

    if not connection:
        return None

    cursor = connection.cursor()

    try:

        guest_id = None

        # ----------------------------------------------
        # TÌM THEO CCCD / PASSPORT
        # ----------------------------------------------

        if id_number:

            cursor.execute("""
                SELECT id
                FROM guests
                WHERE id_number = %s
                LIMIT 1
            """, (id_number,))

            result = cursor.fetchone()

            if result:
                guest_id = result[0]

        # ----------------------------------------------
        # NẾU KHÔNG CÓ THÌ TÌM THEO SỐ ĐIỆN THOẠI
        # ----------------------------------------------

        if guest_id is None and phone:

            cursor.execute("""
                SELECT id
                FROM guests
                WHERE phone = %s
                LIMIT 1
            """, (phone,))

            result = cursor.fetchone()

            if result:
                guest_id = result[0]

        # ----------------------------------------------
        # CẬP NHẬT KHÁCH CŨ
        # ----------------------------------------------

        if guest_id is not None:

            cursor.execute("""
                UPDATE guests
                SET
                    full_name = %s,
                    phone = %s,
                    email = %s,
                    address = %s,
                    nationality = %s
                WHERE id = %s
            """, (
                full_name,
                phone,
                email,
                address,
                nationality,
                guest_id
            ))

        # ----------------------------------------------
        # TẠO KHÁCH MỚI
        # ----------------------------------------------

        else:

            cursor.execute("""
                INSERT INTO guests
                (
                    full_name,
                    id_number,
                    phone,
                    email,
                    address,
                    nationality
                )
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                full_name,
                id_number,
                phone,
                email,
                address,
                nationality
            ))

            guest_id = cursor.lastrowid

        connection.commit()

        return guest_id

    except IntegrityError:

        connection.rollback()
        st.error(
            "Thông tin CCCD/Passport có thể đã tồn tại."
        )

        return None

    except Error as e:

        connection.rollback()
        st.error(f"Lỗi khách hàng: {e}")

        return None

    finally:

        cursor.close()
        connection.close()


# ============================================================
# KIỂM TRA PHÒNG CÓ BỊ TRÙNG LỊCH
# ============================================================

def check_room_available(
    room_id,
    check_in,
    check_out,
    exclude_booking_id=None
):

    connection = get_connection()

    if not connection:
        return False

    cursor = connection.cursor()

    try:

        query = """
            SELECT COUNT(*)
            FROM bookings
            WHERE room_id = %s
            AND booking_status NOT IN ('Đã hủy', 'Cancelled')
            AND check_in < %s
            AND check_out > %s
        """

        params = [
            room_id,
            check_out,
            check_in
        ]

        if exclude_booking_id is not None:

            query += """
                AND id != %s
            """

            params.append(exclude_booking_id)

        cursor.execute(query, tuple(params))

        count = cursor.fetchone()[0]

        return count == 0

    except Error as e:

        st.error(f"Lỗi kiểm tra phòng: {e}")

        return False

    finally:

        cursor.close()
        connection.close()


# ============================================================
# TẠO ĐẶT PHÒNG
# ============================================================

def create_booking(
    guest_id,
    room_id,
    check_in,
    check_out,
    adults,
    children,
    notes
):

    if check_out <= check_in:

        st.error(
            "Ngày trả phòng phải sau ngày nhận phòng."
        )

        return False

    if not check_room_available(
        room_id,
        check_in,
        check_out
    ):

        st.error(
            "Phòng đã có lịch đặt trong khoảng thời gian này."
        )

        return False

    connection = get_connection()

    if not connection:
        return False

    cursor = connection.cursor()

    try:

        cursor.execute("""
            INSERT INTO bookings
            (
                guest_id,
                room_id,
                check_in,
                check_out,
                adults,
                children,
                booking_status,
                notes
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """, (
            guest_id,
            room_id,
            check_in,
            check_out,
            adults,
            children,
            "Đã đặt",
            notes
        ))

        connection.commit()

        return True

    except Error as e:

        connection.rollback()
        st.error(f"Lỗi tạo đặt phòng: {e}")

        return False

    finally:

        cursor.close()
        connection.close()


# ============================================================
# CẬP NHẬT TRẠNG THÁI BOOKING
# ============================================================

def update_booking_status(
    booking_id,
    status
):

    connection = get_connection()

    if not connection:
        return False

    cursor = connection.cursor()

    try:

        cursor.execute("""
            UPDATE bookings
            SET booking_status = %s
            WHERE id = %s
        """, (
            status,
            booking_id
        ))

        connection.commit()

        return True

    except Error as e:

        connection.rollback()
        st.error(
            f"Lỗi cập nhật trạng thái: {e}"
        )

        return False

    finally:

        cursor.close()
        connection.close()


# ============================================================
# THÊM THANH TOÁN
# ============================================================

def add_payment(
    booking_id,
    amount,
    payment_method,
    notes
):

    if amount <= 0:

        st.error(
            "Số tiền thanh toán phải lớn hơn 0."
        )

        return False

    connection = get_connection()

    if not connection:
        return False

    cursor = connection.cursor()

    try:

        # ------------------------------------------------
        # TÍNH TỔNG TIỀN PHÒNG
        # ------------------------------------------------

        cursor.execute("""
            SELECT
                r.price,
                b.check_in,
                b.check_out
            FROM bookings b
            JOIN rooms r
                ON b.room_id = r.id
            WHERE b.id = %s
        """, (booking_id,))

        booking = cursor.fetchone()

        if not booking:

            st.error(
                "Không tìm thấy booking."
            )

            return False

        price = float(booking[0])
        check_in = booking[1]
        check_out = booking[2]

        nights = (
            check_out - check_in
        ).days

        if nights <= 0:
            nights = 1

        total_amount = price * nights

        # ------------------------------------------------
        # TỔNG ĐÃ THANH TOÁN
        # ------------------------------------------------

        cursor.execute("""
            SELECT COALESCE(
                SUM(amount),
                0
            )
            FROM payments
            WHERE booking_id = %s
        """, (booking_id,))

        paid_amount = float(
            cursor.fetchone()[0]
        )

        remaining = (
            total_amount - paid_amount
        )

        if amount > remaining:

            st.error(
                "Số tiền thanh toán vượt quá số tiền còn phải thanh toán."
            )

            return False

        cursor.execute("""
            INSERT INTO payments
            (
                booking_id,
                amount,
                payment_method,
                notes
            )
            VALUES (%s, %s, %s, %s)
        """, (
            booking_id,
            amount,
            payment_method,
            notes
        ))

        connection.commit()

        return True

    except Error as e:

        connection.rollback()
        st.error(
            f"Lỗi thanh toán: {e}"
        )

        return False

    finally:

        cursor.close()
        connection.close()


# ============================================================
# DASHBOARD - THỐNG KÊ
# ============================================================

def get_dashboard_stats():

    connection = get_connection()

    if not connection:
        return {
            "total": 0,
            "available": 0,
            "occupied": 0,
            "reserved": 0,
            "cleaning": 0,
            "maintenance": 0
        }

    cursor = connection.cursor()

    try:

        cursor.execute("""
            SELECT COUNT(*)
            FROM rooms
        """)

        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM rooms
            WHERE status = 'Trống'
        """)

        available = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM rooms
            WHERE status = 'Đang ở'
        """)

        occupied = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM rooms
            WHERE status = 'Đã đặt'
        """)

        reserved = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM rooms
            WHERE status = 'Đang dọn'
        """)

        cleaning = cursor.fetchone()[0]

        cursor.execute("""
            SELECT COUNT(*)
            FROM rooms
            WHERE status = 'Bảo trì'
        """)

        maintenance = cursor.fetchone()[0]

        return {
            "total": total,
            "available": available,
            "occupied": occupied,
            "reserved": reserved,
            "cleaning": cleaning,
            "maintenance": maintenance
        }

    except Error as e:

        st.error(
            f"Lỗi thống kê: {e}"
        )

        return {
            "total": 0,
            "available": 0,
            "occupied": 0,
            "reserved": 0,
            "cleaning": 0,
            "maintenance": 0
        }

    finally:

        cursor.close()
        connection.close()


# ============================================================
# TÍNH TIỀN BOOKING
# ============================================================

def calculate_booking_total(
    room_price,
    check_in,
    check_out
):

    try:

        nights = (
            check_out - check_in
        ).days

        if nights <= 0:
            nights = 1

        return float(room_price) * nights

    except:

        return 0


# ============================================================
# KHỞI TẠO DATABASE
# ============================================================

if "database_initialized" not in st.session_state:

    with st.spinner(
        "Đang kết nối MySQL Aiven..."
    ):

        initialized = init_database()

    st.session_state.database_initialized = initialized

if not st.session_state.database_initialized:

    st.error(
        "Không thể kết nối đến MySQL Aiven."
    )

    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🏨 HOTEL MANAGER")

st.sidebar.markdown(
    "---"
)

menu = st.sidebar.radio(
    "MENU",
    [
        "📊 Tổng quan",
        "🛏️ Quản lý phòng",
        "📅 Đặt phòng",
        "👤 Khách lưu trú",
        "💰 Thanh toán"
    ]
)

st.sidebar.markdown("---")

st.sidebar.info(
    "Hệ thống quản lý khách sạn\n\n"
    "Database: MySQL Aiven"
)


# ============================================================
# TRANG TỔNG QUAN
# ============================================================

if menu == "📊 Tổng quan":

    st.title(
        "📊 Tổng quan khách sạn"
    )

    st.caption(
        "Hệ thống quản lý phòng, khách lưu trú, đặt phòng và thanh toán"
    )

    stats = get_dashboard_stats()

    col1, col2, col3, col4 = st.columns(4)

    with col1:

        st.metric(
            "🏨 Tổng số phòng",
            stats["total"]
        )

    with col2:

        st.metric(
            "🟢 Phòng trống",
            stats["available"]
        )

    with col3:

        st.metric(
            "🔴 Đang ở",
            stats["occupied"]
        )

    with col4:

        st.metric(
            "🟡 Đã đặt",
            stats["reserved"]
        )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:

        st.subheader(
            "Tình trạng phòng"
        )

        status_data = pd.DataFrame({
            "Trạng thái": [
                "Trống",
                "Đang ở",
                "Đã đặt",
                "Đang dọn",
                "Bảo trì"
            ],
            "Số lượng": [
                stats["available"],
                stats["occupied"],
                stats["reserved"],
                stats["cleaning"],
                stats["maintenance"]
            ]
        })

        st.dataframe(
            status_data,
            use_container_width=True,
            hide_index=True
        )

    with col2:

        st.subheader(
            "Biểu đồ phòng"
        )

        chart_data = pd.DataFrame({
            "Số lượng": [
                stats["available"],
                stats["occupied"],
                stats["reserved"],
                stats["cleaning"],
                stats["maintenance"]
            ]
        }, index=[
            "Trống",
            "Đang ở",
            "Đã đặt",
            "Đang dọn",
            "Bảo trì"
        ])

        st.bar_chart(
            chart_data
        )

    st.markdown("---")

    st.subheader(
        "🗺️ Sơ đồ phòng"
    )

    rooms = get_rooms()

    if not rooms.empty:

        floors = sorted(
            rooms["floor"].dropna().unique()
        )

        for floor in floors:

            st.markdown(
                f"### Tầng {int(floor)}"
            )

            floor_rooms = rooms[
                rooms["floor"] == floor
            ]

            cols = st.columns(
                min(
                    len(floor_rooms),
                    6
                )
            )

            for index, (_, room) in enumerate(
                floor_rooms.iterrows()
            ):

                with cols[
                    index % len(cols)
                ]:

                    status = room["status"]

                    if status == "Trống":
                        icon = "🟢"

                    elif status == "Đang ở":
                        icon = "🔴"

                    elif status == "Đã đặt":
                        icon = "🟡"

                    elif status == "Đang dọn":
                        icon = "🔵"

                    else:
                        icon = "⚫"

                    st.metric(
                        f"{icon} Phòng {room['room_number']}",
                        room["room_type"],
                        format_money(
                            room["price"]
                        )
                    )

                    st.caption(
                        status
                    )


# ============================================================
# QUẢN LÝ PHÒNG
# ============================================================

elif menu == "🛏️ Quản lý phòng":

    st.title(
        "🛏️ Quản lý phòng"
    )

    tab1, tab2 = st.tabs(
        [
            "📋 Danh sách phòng",
            "➕ Thêm phòng"
        ]
    )

    # ========================================================
    # DANH SÁCH PHÒNG
    # ========================================================

    with tab1:

        rooms = get_rooms()

        if rooms.empty:

            st.warning(
                "Chưa có dữ liệu phòng."
            )

        else:

            col1, col2 = st.columns(2)

            with col1:

                status_filter = st.selectbox(
                    "Lọc theo trạng thái",
                    [
                        "Tất cả",
                        "Trống",
                        "Đang ở",
                        "Đã đặt",
                        "Đang dọn",
                        "Bảo trì"
                    ]
                )

            with col2:

                room_type_filter = st.selectbox(
                    "Lọc theo loại phòng",
                    [
                        "Tất cả"
                    ] + sorted(
                        rooms["room_type"]
                        .dropna()
                        .unique()
                        .tolist()
                    )
                )

            filtered_rooms = rooms.copy()

            if status_filter != "Tất cả":

                filtered_rooms = filtered_rooms[
                    filtered_rooms["status"]
                    == status_filter
                ]

            if room_type_filter != "Tất cả":

                filtered_rooms = filtered_rooms[
                    filtered_rooms["room_type"]
                    == room_type_filter
                ]

            display_rooms = filtered_rooms.copy()

            display_rooms["price"] = (
                display_rooms["price"]
                .apply(format_money)
            )

            display_rooms = display_rooms[
                [
                    "id",
                    "room_number",
                    "room_type",
                    "price",
                    "status",
                    "floor",
                    "description"
                ]
            ]

            display_rooms.columns = [
                "ID",
                "Số phòng",
                "Loại phòng",
                "Giá/đêm",
                "Trạng thái",
                "Tầng",
                "Mô tả"
            ]

            st.dataframe(
                display_rooms,
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")

            st.subheader(
                "✏️ Chỉnh sửa phòng"
            )

            if not filtered_rooms.empty:

                room_options = {
                    f"Phòng {row.room_number} - {row.room_type}":
                    row.id
                    for row in filtered_rooms.itertuples()
                }

                selected_room_label = st.selectbox(
                    "Chọn phòng",
                    list(room_options.keys())
                )

                selected_room_id = room_options[
                    selected_room_label
                ]

                selected_room = filtered_rooms[
                    filtered_rooms["id"]
                    == selected_room_id
                ].iloc[0]

                c1, c2 = st.columns(2)

                with c1:

                    edit_room_number = st.text_input(
                        "Số phòng",
                        value=str(
                            selected_room["room_number"]
                        )
                    )

                    edit_room_type = st.selectbox(
                        "Loại phòng",
                        [
                            "Standard",
                            "Deluxe",
                            "Superior",
                            "Suite",
                            "VIP",
                            "Family",
                            "Presidential"
                        ],
                        index=(
                            [
                                "Standard",
                                "Deluxe",
                                "Superior",
                                "Suite",
                                "VIP",
                                "Family",
                                "Presidential"
                            ].index(
                                selected_room["room_type"]
                            )
                            if selected_room["room_type"]
                            in [
                                "Standard",
                                "Deluxe",
                                "Superior",
                                "Suite",
                                "VIP",
                                "Family",
                                "Presidential"
                            ]
                            else 0
                        )
                    )

                    edit_price = st.number_input(
                        "Giá phòng / đêm",
                        min_value=0.0,
                        value=float(
                            selected_room["price"]
                        ),
                        step=100000.0
                    )

                with c2:

                    edit_status = st.selectbox(
                        "Trạng thái",
                        [
                            "Trống",
                            "Đang ở",
                            "Đã đặt",
                            "Đang dọn",
                            "Bảo trì"
                        ],
                        index=(
                            [
                                "Trống",
                                "Đang ở",
                                "Đã đặt",
                                "Đang dọn",
                                "Bảo trì"
                            ].index(
                                selected_room["status"]
                            )
                            if selected_room["status"]
                            in [
                                "Trống",
                                "Đang ở",
                                "Đã đặt",
                                "Đang dọn",
                                "Bảo trì"
                            ]
                            else 0
                        )
                    )

                    edit_floor = st.number_input(
                        "Tầng",
                        min_value=1,
                        max_value=100,
                        value=int(
                            selected_room["floor"]
                        )
                    )

                    edit_description = st.text_area(
                        "Mô tả",
                        value=(
                            selected_room["description"]
                            or ""
                        )
                    )

                col_update, col_delete = st.columns(2)

                with col_update:

                    if st.button(
                        "💾 Lưu thay đổi",
                        use_container_width=True
                    ):

                        success = update_room(
                            selected_room_id,
                            edit_room_number,
                            edit_room_type,
                            edit_price,
                            edit_status,
                            edit_floor,
                            edit_description
                        )

                        if success:

                            st.success(
                                "Đã cập nhật phòng."
                            )

                            st.rerun()

                with col_delete:

                    if st.button(
                        "🗑️ Xóa phòng",
                        use_container_width=True
                    ):

                        success = delete_room(
                            selected_room_id
                        )

                        if success:

                            st.success(
                                "Đã xóa phòng."
                            )

                            st.rerun()

    # ========================================================
    # THÊM PHÒNG
    # ========================================================

    with tab2:

        st.subheader(
            "➕ Thêm phòng mới"
        )

        c1, c2 = st.columns(2)

        with c1:

            new_room_number = st.text_input(
                "Số phòng *",
                placeholder="Ví dụ: 405"
            )

            new_room_type = st.selectbox(
                "Loại phòng *",
                [
                    "Standard",
                    "Deluxe",
                    "Superior",
                    "Suite",
                    "VIP",
                    "Family",
                    "Presidential"
                ]
            )

            new_room_price = st.number_input(
                "Giá phòng / đêm *",
                min_value=0.0,
                value=800000.0,
                step=100000.0
            )

        with c2:

            new_room_floor = st.number_input(
                "Tầng *",
                min_value=1,
                max_value=100,
                value=1
            )

            new_room_description = st.text_area(
                "Mô tả"
            )

        if st.button(
            "➕ Thêm phòng",
            type="primary",
            use_container_width=True
        ):

            if not new_room_number.strip():

                st.error(
                    "Vui lòng nhập số phòng."
                )

            elif new_room_price <= 0:

                st.error(
                    "Giá phòng phải lớn hơn 0."
                )

            else:

                success = add_room(
                    new_room_number.strip(),
                    new_room_type,
                    new_room_price,
                    new_room_floor,
                    new_room_description
                )

                if success:

                    st.success(
                        f"Đã thêm phòng {new_room_number}."
                    )

                    st.rerun()


# ============================================================
# ĐẶT PHÒNG
# ============================================================

elif menu == "📅 Đặt phòng":

    st.title(
        "📅 Đặt phòng"
    )

    tab1, tab2 = st.tabs(
        [
            "➕ Tạo đặt phòng",
            "📋 Danh sách đặt phòng"
        ]
    )

    # ========================================================
    # TẠO BOOKING
    # ========================================================

    with tab1:

        st.subheader(
            "Thông tin khách"
        )

        c1, c2 = st.columns(2)

        with c1:

            guest_name = st.text_input(
                "Họ và tên *"
            )

            guest_id_number = st.text_input(
                "CCCD / Passport"
            )

            guest_phone = st.text_input(
                "Số điện thoại"
            )

            guest_email = st.text_input(
                "Email"
            )

        with c2:

            guest_nationality = st.text_input(
                "Quốc tịch",
                value="Việt Nam"
            )

            guest_address = st.text_area(
                "Địa chỉ"
            )

        st.markdown("---")

        st.subheader(
            "Thông tin đặt phòng"
        )

        rooms = get_rooms()

        available_rooms = rooms[
            rooms["status"] != "Bảo trì"
        ].copy()

        if available_rooms.empty:

            st.warning(
                "Hiện chưa có phòng khả dụng."
            )

        else:

            room_options = {
                (
                    f"Phòng {row.room_number} - "
                    f"{row.room_type} - "
                    f"{format_money(row.price)}/đêm"
                ):
                row.id
                for row in available_rooms.itertuples()
            }

            selected_room_label = st.selectbox(
                "Chọn phòng *",
                list(room_options.keys())
            )

            selected_room_id = room_options[
                selected_room_label
            ]

            selected_room_data = available_rooms[
                available_rooms["id"]
                == selected_room_id
            ].iloc[0]

            c1, c2 = st.columns(2)

            with c1:

                check_in = st.date_input(
                    "Ngày nhận phòng *",
                    value=date.today()
                )

                adults = st.number_input(
                    "Số người lớn",
                    min_value=1,
                    max_value=20,
                    value=1
                )

            with c2:

                check_out = st.date_input(
                    "Ngày trả phòng *",
                    value=date.today()
                )

                children = st.number_input(
                    "Số trẻ em",
                    min_value=0,
                    max_value=20,
                    value=0
                )

            notes = st.text_area(
                "Ghi chú"
            )

            if check_out > check_in:

                total = calculate_booking_total(
                    selected_room_data["price"],
                    check_in,
                    check_out
                )

                nights = (
                    check_out - check_in
                ).days

                st.info(
                    f"🛏️ {nights} đêm × "
                    f"{format_money(selected_room_data['price'])} "
                    f"= **{format_money(total)}**"
                )

            else:

                st.warning(
                    "Ngày trả phòng phải sau ngày nhận phòng."
                )

            if st.button(
                "📅 Xác nhận đặt phòng",
                type="primary",
                use_container_width=True
            ):

                if not guest_name.strip():

                    st.error(
                        "Vui lòng nhập tên khách."
                    )

                elif not guest_phone.strip():

                    st.error(
                        "Vui lòng nhập số điện thoại."
                    )

                elif check_out <= check_in:

                    st.error(
                        "Ngày trả phòng không hợp lệ."
                    )

                else:

                    guest_id = get_or_create_guest(
                        guest_name.strip(),
                        guest_id_number.strip(),
                        guest_phone.strip(),
                        guest_email.strip(),
                        guest_address.strip(),
                        guest_nationality.strip()
                    )

                    if guest_id:

                        success = create_booking(
                            guest_id,
                            selected_room_id,
                            check_in,
                            check_out,
                            adults,
                            children,
                            notes
                        )

                        if success:

                            st.success(
                                "🎉 Đặt phòng thành công!"
                            )

                            st.rerun()

    # ========================================================
    # DANH SÁCH BOOKING
    # ========================================================

    with tab2:

        bookings = get_bookings()

        if bookings.empty:

            st.info(
                "Chưa có đặt phòng."
            )

        else:

            display_bookings = bookings.copy()

            display_bookings["price"] = (
                display_bookings["price"]
                .apply(format_money)
            )

            display_bookings = display_bookings[
                [
                    "id",
                    "full_name",
                    "phone",
                    "room_number",
                    "room_type",
                    "price",
                    "check_in",
                    "check_out",
                    "adults",
                    "children",
                    "booking_status",
                    "notes"
                ]
            ]

            display_bookings.columns = [
                "ID",
                "Khách",
                "Điện thoại",
                "Phòng",
                "Loại phòng",
                "Giá/đêm",
                "Nhận phòng",
                "Trả phòng",
                "Người lớn",
                "Trẻ em",
                "Trạng thái",
                "Ghi chú"
            ]

            st.dataframe(
                display_bookings,
                use_container_width=True,
                hide_index=True
            )

            st.markdown("---")

            st.subheader(
                "🔄 Cập nhật trạng thái đặt phòng"
            )

            booking_options = {
                (
                    f"#{row.id} - "
                    f"{row.full_name} - "
                    f"Phòng {row.room_number}"
                ):
                row.id
                for row in bookings.itertuples()
            }

            selected_booking_label = st.selectbox(
                "Chọn booking",
                list(booking_options.keys())
            )

            selected_booking_id = booking_options[
                selected_booking_label
            ]

            current_booking = bookings[
                bookings["id"]
                == selected_booking_id
            ].iloc[0]

            new_status = st.selectbox(
                "Trạng thái mới",
                [
                    "Đã đặt",
                    "Đã xác nhận",
                    "Đã nhận phòng",
                    "Đã trả phòng",
                    "Đã hủy"
                ],
                index=(
                    [
                        "Đã đặt",
                        "Đã xác nhận",
                        "Đã nhận phòng",
                        "Đã trả phòng",
                        "Đã hủy"
                    ].index(
                        current_booking["booking_status"]
                    )
                    if current_booking["booking_status"]
                    in [
                        "Đã đặt",
                        "Đã xác nhận",
                        "Đã nhận phòng",
                        "Đã trả phòng",
                        "Đã hủy"
                    ]
                    else 0
                )
            )

            if st.button(
                "🔄 Cập nhật trạng thái",
                use_container_width=True
            ):

                success = update_booking_status(
                    selected_booking_id,
                    new_status
                )

                if success:

                    st.success(
                        "Đã cập nhật trạng thái."
                    )

                    st.rerun()


# ============================================================
# KHÁCH LƯU TRÚ
# ============================================================

elif menu == "👤 Khách lưu trú":

    st.title(
        "👤 Khách lưu trú"
    )

    guests = get_guests()

    if guests.empty:

        st.info(
            "Chưa có thông tin khách hàng."
        )

    else:

        search = st.text_input(
            "🔎 Tìm kiếm khách hàng",
            placeholder="Nhập tên, CCCD hoặc số điện thoại..."
        )

        filtered_guests = guests.copy()

        if search.strip():

            search_lower = search.lower()

            filtered_guests = filtered_guests[
                filtered_guests[
                    [
                        "full_name",
                        "id_number",
                        "phone"
                    ]
                ]
                .fillna("")
                .astype(str)
                .apply(
                    lambda row:
                    row.str.lower()
                    .str.contains(
                        search_lower,
                        regex=False
                    )
                    .any(),
                    axis=1
                )
            ]

        st.metric(
            "Tổng số khách",
            len(filtered_guests)
        )

        display_guests = filtered_guests.copy()

        display_guests.columns = [
            "ID",
            "Họ tên",
            "CCCD / Passport",
            "Điện thoại",
            "Email",
            "Địa chỉ",
            "Quốc tịch",
            "Ngày tạo"
        ]

        st.dataframe(
            display_guests,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")

        st.subheader(
            "📋 Lịch sử đặt phòng"
        )

        bookings = get_bookings()

        if not bookings.empty:

            guest_names = sorted(
                bookings[
                    "full_name"
                ]
                .dropna()
                .unique()
                .tolist()
            )

            selected_guest = st.selectbox(
                "Chọn khách",
                guest_names
            )

            guest_bookings = bookings[
                bookings["full_name"]
                == selected_guest
            ].copy()

            guest_bookings["price"] = (
                guest_bookings["price"]
                .apply(format_money)
            )

            st.dataframe(
                guest_bookings[
                    [
                        "id",
                        "room_number",
                        "room_type",
                        "check_in",
                        "check_out",
                        "booking_status",
                        "price"
                    ]
                ],
                use_container_width=True,
                hide_index=True
            )


# ============================================================
# THANH TOÁN
# ============================================================

elif menu == "💰 Thanh toán":

    st.title(
        "💰 Thanh toán"
    )

    bookings = get_bookings()

    if bookings.empty:

        st.info(
            "Chưa có booking để thanh toán."
        )

    else:

        st.subheader(
            "➕ Tạo thanh toán"
        )

        booking_options = {}

        for row in bookings.itertuples():

            if row.booking_status == "Đã hủy":
                continue

            booking_options[
                (
                    f"#{row.id} - "
                    f"{row.full_name} - "
                    f"Phòng {row.room_number} - "
                    f"{row.check_in} → {row.check_out}"
                )
            ] = row.id

        if not booking_options:

            st.warning(
                "Không có booking hợp lệ."
            )

        else:

            selected_payment_label = st.selectbox(
                "Chọn booking",
                list(booking_options.keys())
            )

            selected_payment_booking_id = booking_options[
                selected_payment_label
            ]

            selected_booking = bookings[
                bookings["id"]
                == selected_payment_booking_id
            ].iloc[0]

            room_price = float(
                selected_booking["price"]
            )

            check_in = selected_booking[
                "check_in"
            ]

            check_out = selected_booking[
                "check_out"
            ]

            total_amount = calculate_booking_total(
                room_price,
                check_in,
                check_out
            )

            # --------------------------------------------
            # LẤY ĐÃ THANH TOÁN
            # --------------------------------------------

            connection = get_connection()

            paid_amount = 0

            if connection:

                cursor = connection.cursor()

                try:

                    cursor.execute("""
                        SELECT
                            COALESCE(
                                SUM(amount),
                                0
                            )
                        FROM payments
                        WHERE booking_id = %s
                    """, (
                        selected_payment_booking_id,
                    ))

                    paid_amount = float(
                        cursor.fetchone()[0]
                    )

                except Error as e:

                    st.error(
                        f"Lỗi lấy thanh toán: {e}"
                    )

                finally:

                    cursor.close()
                    connection.close()

            remaining_amount = (
                total_amount - paid_amount
            )

            c1, c2, c3 = st.columns(3)

            with c1:

                st.metric(
                    "Tổng tiền",
                    format_money(
                        total_amount
                    )
                )

            with c2:

                st.metric(
                    "Đã thanh toán",
                    format_money(
                        paid_amount
                    )
                )

            with c3:

                st.metric(
                    "Còn lại",
                    format_money(
                        remaining_amount
                    )
                )

            st.markdown("---")

            payment_amount = st.number_input(
                "Số tiền thanh toán",
                min_value=0.0,
                max_value=max(
                    remaining_amount,
                    0.0
                ),
                value=(
                    max(
                        remaining_amount,
                        0.0
                    )
                    if remaining_amount > 0
                    else 0.0
                ),
                step=100000.0
            )

            payment_method = st.selectbox(
                "Phương thức thanh toán",
                [
                    "Tiền mặt",
                    "Chuyển khoản",
                    "Thẻ tín dụng",
                    "Thẻ ghi nợ",
                    "Ví điện tử"
                ]
            )

            payment_notes = st.text_area(
                "Ghi chú thanh toán"
            )

            if st.button(
                "💳 Xác nhận thanh toán",
                type="primary",
                use_container_width=True
            ):

                if remaining_amount <= 0:

                    st.warning(
                        "Booking này đã thanh toán đủ."
                    )

                elif payment_amount <= 0:

                    st.error(
                        "Vui lòng nhập số tiền thanh toán."
                    )

                else:

                    success = add_payment(
                        selected_payment_booking_id,
                        payment_amount,
                        payment_method,
                        payment_notes
                    )

                    if success:

                        st.success(
                            "💰 Thanh toán thành công!"
                        )

                        st.rerun()

    st.markdown("---")

    st.subheader(
        "📋 Lịch sử thanh toán"
    )

    payments = get_payments()

    if payments.empty:

        st.info(
            "Chưa có giao dịch thanh toán."
        )

    else:

        display_payments = payments.copy()

        display_payments["amount"] = (
            display_payments["amount"]
            .apply(format_money)
        )

        display_payments.columns = [
            "ID",
            "Booking ID",
            "Khách hàng",
            "Phòng",
            "Số tiền",
            "Phương thức",
            "Ngày thanh toán",
            "Ghi chú"
        ]

        st.dataframe(
            display_payments,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "🏨 Hotel Manager • Streamlit + MySQL Aiven"
)
