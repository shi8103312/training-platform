"""
Database Seed Script - Initialize test data
"""
import sys
sys.path.insert(0, 'backend')

from datetime import datetime, timedelta
import uuid
import json

from app.database import SessionLocal
from app.models.user import User
from app.models.department import Department
from app.models.training import Project, Material
from app.models.exam import Exam, Question
from app.models.notification import Notification
from app.core.security import hash_password


def seed_database():
    db = SessionLocal()

    try:
        # Check if projects already exist
        existing_projects = db.query(Project).count()
        if existing_projects > 0:
            print("Database already has projects, skipping seed...")
            return

        print("Seeding database...")

        # Create departments
        departments = [
            Department(dept_id='D001', dept_name='集团', dept_code='GROUP', parent_id=None, dept_level=1, status=1, sort_order=1),
            Department(dept_id='D002', dept_name='技术部', dept_code='TECH', parent_id='D001', dept_level=2, status=1, sort_order=1),
            Department(dept_id='D003', dept_name='产品部', dept_code='PRODUCT', parent_id='D001', dept_level=2, status=1, sort_order=2),
            Department(dept_id='D004', dept_name='市场部', dept_code='MARKET', parent_id='D001', dept_level=2, status=1, sort_order=3),
            Department(dept_id='D005', dept_name='人力资源部', dept_code='HR', parent_id='D001', dept_level=2, status=1, sort_order=4),
        ]
        for dept in departments:
            existing = db.query(Department).filter(Department.dept_id == dept.dept_id).first()
            if not existing:
                db.add(dept)

        db.commit()
        print(f"Created {len(departments)} departments")

        # Create users
        users = [
            User(
                user_id='admin001',
                dept_id='D005',
                username='admin',
                password_hash=hash_password('admin123'),
                real_name='系统管理员',
                email='admin@company.com',
                role=1,  # HR Admin
                status=1,
            ),
            User(
                user_id='U001',
                dept_id='D002',
                username='zhangsan',
                password_hash=hash_password('123456'),
                real_name='张明华',
                email='zhangsan@company.com',
                role=2,  # Employee
                status=1,
            ),
            User(
                user_id='U002',
                dept_id='D003',
                username='lisi',
                password_hash=hash_password('123456'),
                real_name='李晓燕',
                email='lisi@company.com',
                role=2,
                status=1,
            ),
            User(
                user_id='U003',
                dept_id='D002',
                username='wangwu',
                password_hash=hash_password('123456'),
                real_name='王建国',
                email='wangwu@company.com',
                role=2,
                status=1,
            ),
            User(
                user_id='U004',
                dept_id='D004',
                username='zhaoliu',
                password_hash=hash_password('123456'),
                real_name='赵敏',
                email='zhaoliu@company.com',
                role=2,
                status=1,
            ),
        ]
        for user in users:
            existing = db.query(User).filter(User.user_id == user.user_id).first()
            if not existing:
                db.add(user)

        db.commit()
        print(f"Created {len(users)} users")

        # Create training projects
        projects = [
            Project(
                project_id='P001',
                title='新员工入职培训',
                description='帮助新员工快速了解公司文化、规章制度和基本工作流程',
                status=1,  # Published
                is_required=1,
                push_scope=json.dumps({"type": "all"}),
                deadline=datetime.now() + timedelta(days=30),
                created_by='admin001',
                published_at=datetime.now() - timedelta(days=7),
            ),
            Project(
                project_id='P002',
                title='信息安全意识培训',
                description='提高员工信息安全意识，了解常见网络安全威胁',
                status=1,
                is_required=1,
                push_scope=json.dumps({"type": "all"}),
                deadline=datetime.now() + timedelta(days=15),
                created_by='admin001',
                published_at=datetime.now() - timedelta(days=14),
            ),
            Project(
                project_id='P003',
                title='职业技能提升课程',
                description='提升员工专业技能和工作效率',
                status=1,
                is_required=0,
                push_scope=json.dumps({"type": "departments", "dept_ids": ["D002", "D003"]}),
                deadline=datetime.now() + timedelta(days=45),
                created_by='admin001',
                published_at=datetime.now() - timedelta(days=10),
            ),
        ]
        for project in projects:
            existing = db.query(Project).filter(Project.project_id == project.project_id).first()
            if not existing:
                db.add(project)

        db.commit()
        print(f"Created {len(projects)} projects")

        # Create materials for P001
        materials_p001 = [
            Material(
                material_id='M001',
                project_id='P001',
                title='公司介绍与发展历程',
                material_type=1,  # Video
                storage_path='videos/company_intro.mp4',
                duration=750,  # 12:30
                file_size=52428800,
                file_extension='mp4',
                mime_type='video/mp4',
                sort_order=1,
            ),
            Material(
                material_id='M002',
                project_id='P001',
                title='企业文化与价值观',
                material_type=1,
                storage_path='videos/culture.mp4',
                duration=525,  # 8:45
                file_size=35000000,
                file_extension='mp4',
                mime_type='video/mp4',
                sort_order=2,
            ),
            Material(
                material_id='M003',
                project_id='P001',
                title='组织架构与部门职责',
                material_type=1,
                storage_path='videos/org_structure.mp4',
                duration=920,  # 15:20
                file_size=62000000,
                file_extension='mp4',
                mime_type='video/mp4',
                sort_order=3,
            ),
            Material(
                material_id='M004',
                project_id='P001',
                title='员工手册与规章制度',
                material_type=2,  # Document
                storage_path='docs/employee_handbook.pdf',
                duration=0,
                file_size=1500000,
                file_extension='pdf',
                mime_type='application/pdf',
                sort_order=4,
            ),
            Material(
                material_id='M005',
                project_id='P001',
                title='薪酬福利体系说明',
                material_type=2,
                storage_path='docs/salary_benefits.docx',
                duration=0,
                file_size=800000,
                file_extension='docx',
                mime_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                sort_order=5,
            ),
        ]
        for material in materials_p001:
            existing = db.query(Material).filter(Material.material_id == material.material_id).first()
            if not existing:
                db.add(material)

        # Materials for P002
        materials_p002 = [
            Material(
                material_id='M006',
                project_id='P002',
                title='网络安全基础',
                material_type=1,
                storage_path='videos/network_security.mp4',
                duration=1200,
                file_size=80000000,
                file_extension='mp4',
                mime_type='video/mp4',
                sort_order=1,
            ),
            Material(
                material_id='M007',
                project_id='P002',
                title='密码安全与账户管理',
                material_type=1,
                storage_path='videos/password_security.mp4',
                duration=900,
                file_size=60000000,
                file_extension='mp4',
                mime_type='video/mp4',
                sort_order=2,
            ),
            Material(
                material_id='M008',
                project_id='P002',
                title='防范钓鱼攻击',
                material_type=1,
                storage_path='videos/phishing.mp4',
                duration=780,
                file_size=52000000,
                file_extension='mp4',
                mime_type='video/mp4',
                sort_order=3,
            ),
        ]
        for material in materials_p002:
            existing = db.query(Material).filter(Material.material_id == material.material_id).first()
            if not existing:
                db.add(material)

        db.commit()
        print(f"Created materials for projects")

        # Create exams
        exams = [
            Exam(
                exam_id='E001',
                project_id='P001',
                title='新员工入职培训结业考试',
                description='测试对公司基本情况的了解程度',
                duration_minutes=60,
                passing_score=60,
                total_score=100,
                question_count=5,
                attempt_limit=1,
            ),
            Exam(
                exam_id='E002',
                project_id='P002',
                title='信息安全意识考核',
                description='测试信息安全知识掌握程度',
                duration_minutes=45,
                passing_score=70,
                total_score=100,
                question_count=4,
                attempt_limit=3,
            ),
        ]
        for exam in exams:
            existing = db.query(Exam).filter(Exam.exam_id == exam.exam_id).first()
            if not existing:
                db.add(exam)

        db.commit()
        print(f"Created exams")

        # Create questions for E001
        questions_e001 = [
            Question(
                question_id='Q001',
                exam_id='E001',
                question_text='公司的全称是什么？',
                question_type=1,  # Single choice
                score=20,
                options=json.dumps([
                    {'key': 'A', 'text': '某某集团有限公司', 'correct': True},
                    {'key': 'B', 'text': '某某科技有限公司', 'correct': False},
                    {'key': 'C', 'text': '某某股份有限公司', 'correct': False},
                    {'key': 'D', 'text': '某某企业有限公司', 'correct': False},
                ]),
            ),
            Question(
                question_id='Q002',
                exam_id='E001',
                question_text='以下哪些属于公司核心价值观？（多选）',
                question_type=2,  # Multiple choice
                score=20,
                options=json.dumps([
                    {'key': 'A', 'text': '创新', 'correct': True},
                    {'key': 'B', 'text': '合作', 'correct': True},
                    {'key': 'C', 'text': '激进', 'correct': False},
                    {'key': 'D', 'text': '责任', 'correct': True},
                ]),
            ),
            Question(
                question_id='Q003',
                exam_id='E001',
                question_text='新员工入职培训是必修课程。',
                question_type=3,  # True/False
                score=20,
                options=json.dumps([
                    {'key': 'A', 'text': '正确', 'correct': True},
                    {'key': 'B', 'text': '错误', 'correct': False},
                ]),
            ),
            Question(
                question_id='Q004',
                exam_id='E001',
                question_text='请简述员工旷工的处理规定（填空题）',
                question_type=4,  # Fill in blank
                score=20,
                options=json.dumps([]),
            ),
            Question(
                question_id='Q005',
                exam_id='E001',
                question_text='请描述公司的发展历程（简答题）',
                question_type=5,  # Essay
                score=20,
                options=json.dumps([]),
            ),
        ]
        for question in questions_e001:
            existing = db.query(Question).filter(Question.question_id == question.question_id).first()
            if not existing:
                db.add(question)

        # Questions for E002
        questions_e002 = [
            Question(
                question_id='Q006',
                exam_id='E002',
                question_text='以下哪个是强密码的特征？',
                question_type=1,
                score=25,
                options=json.dumps([
                    {'key': 'A', 'text': '包含姓名和生日', 'correct': False},
                    {'key': 'B', 'text': '包含大小写字母、数字和特殊字符', 'correct': True},
                    {'key': 'C', 'text': '使用"123456"格式', 'correct': False},
                    {'key': 'D', 'text': '使用简单的单词', 'correct': False},
                ]),
            ),
            Question(
                question_id='Q007',
                exam_id='E002',
                question_text='钓鱼邮件的特征包括？（多选）',
                question_type=2,
                score=25,
                options=json.dumps([
                    {'key': 'A', 'text': '发件人地址可疑', 'correct': True},
                    {'key': 'B', 'text': '要求点击链接', 'correct': True},
                    {'key': 'C', 'text': '来自官方域名', 'correct': False},
                    {'key': 'D', 'text': '制造紧迫感', 'correct': True},
                ]),
            ),
            Question(
                question_id='Q008',
                exam_id='E002',
                question_text='发现安全漏洞应该及时报告给IT部门。',
                question_type=3,
                score=25,
                options=json.dumps([
                    {'key': 'A', 'text': '正确', 'correct': True},
                    {'key': 'B', 'text': '错误', 'correct': False},
                ]),
            ),
            Question(
                question_id='Q009',
                exam_id='E002',
                question_text='请简述如何识别钓鱼邮件（简答题）',
                question_type=5,
                score=25,
                options=json.dumps([]),
            ),
        ]
        for question in questions_e002:
            existing = db.query(Question).filter(Question.question_id == question.question_id).first()
            if not existing:
                db.add(question)

        db.commit()
        print(f"Created questions for exams")

        # Create some notifications for users
        notifications = [
            Notification(
                notif_id='N001',
                user_id='U001',
                notif_type=1,
                title='【培训通知】新员工入职培训',
                content='您有一项新的培训任务等待完成。\n培训项目：新员工入职培训\n截止日期：2026-06-07\n【必修】请在截止日期前完成培训！',
                project_id='P001',
                email_status=1,
                read_status=0,
            ),
            Notification(
                notif_id='N002',
                user_id='U001',
                notif_type=2,
                title='【截止提醒】新员工入职培训即将截止',
                content='您参加的《新员工入职培训》将在3天后截止，请尽快完成！',
                project_id='P001',
                email_status=1,
                read_status=0,
            ),
            Notification(
                notif_id='N003',
                user_id='U002',
                notif_type=1,
                title='【培训通知】信息安全意识培训',
                content='您有一项新的培训任务等待完成。\n培训项目：信息安全意识培训\n截止日期：2026-05-23\n【必修】请在截止日期前完成培训！',
                project_id='P002',
                email_status=1,
                read_status=1,
            ),
        ]
        for notif in notifications:
            existing = db.query(Notification).filter(Notification.notif_id == notif.notif_id).first()
            if not existing:
                db.add(notif)

        db.commit()
        print(f"Created {len(notifications)} notifications")

        print("Database seeding completed successfully!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == '__main__':
    seed_database()
