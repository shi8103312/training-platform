"""
Exam API Routes
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import json
import random

from ...database import get_db
from ...models.user import User
from ...models.training import Project, Material, WatchProgress
from ...models.exam import Exam, Question, ExamAttempt
from ...api.deps import get_current_user, require_hr_admin
from ...core.permissions import Role
from ...schemas.training import CreateExamRequest, QuestionSchema

router = APIRouter(prefix="/exam", tags=["考试"])


@router.post("")
async def create_exam(
    exam_data: CreateExamRequest,
    current_user: User = Depends(require_hr_admin()),
    db: Session = Depends(get_db),
):
    """
    Create a new exam for a project (HR admin only).
    """
    # Validate project exists
    project = db.query(Project).filter(
        Project.project_id == exam_data.project_id,
        Project.is_deleted == 0,
    ).first()

    if not project:
        return {
            "code": 20001,
            "message": "项目不存在",
        }

    # Check if project already has an exam
    existing = db.query(Exam).filter(
        Exam.project_id == exam_data.project_id,
        Exam.is_deleted == 0,
    ).first()

    if existing:
        return {
            "code": 50001,
            "message": "该项目已存在考试",
        }

    # Generate exam ID
    exam_id = f"E{uuid.uuid4().hex[:8].upper()}"

    # Calculate total score
    total_score = sum(q.score for q in exam_data.questions)

    # Create exam
    exam = Exam(
        exam_id=exam_id,
        project_id=exam_data.project_id,
        title=exam_data.title,
        description=exam_data.description,
        passing_score=exam_data.passing_score,
        duration_minutes=exam_data.duration_minutes,
        attempt_limit=exam_data.attempt_limit,
        random_shuffle=1 if exam_data.random_shuffle else 0,
        show_answer=1 if exam_data.show_answer else 0,
        total_score=total_score,
        question_count=len(exam_data.questions),
    )

    db.add(exam)

    # Create questions
    for idx, q in enumerate(exam_data.questions):
        question_id = f"Q{uuid.uuid4().hex[:8].upper()}"
        question = Question(
            question_id=question_id,
            exam_id=exam_id,
            question_type=q.question_type,
            question_text=q.question_text,
            options=json.dumps([opt.model_dump() for opt in q.options]) if q.options else None,
            correct_answer=q.correct_answer,
            score=q.score,
            explanation=q.explanation,
            sort_order=idx,
        )
        db.add(question)

    db.commit()

    return {
        "code": 0,
        "data": {
            "exam_id": exam_id,
        },
    }


@router.get("/{exam_id}")
async def get_exam_detail(
    exam_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get exam detail.
    """
    exam = db.query(Exam).filter(
        Exam.exam_id == exam_id,
        Exam.is_deleted == 0,
    ).first()

    if not exam:
        return {
            "code": 50001,
            "message": "考试不存在",
        }

    return {
        "code": 0,
        "data": {
            "exam_id": exam.exam_id,
            "project_id": exam.project_id,
            "title": exam.title,
            "description": exam.description,
            "passing_score": exam.passing_score,
            "duration_minutes": exam.duration_minutes,
            "attempt_limit": exam.attempt_limit,
            "total_score": exam.total_score,
            "question_count": exam.question_count,
            "status": exam.status,
        },
    }


@router.post("/{exam_id}/start")
async def start_exam(
    exam_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Start an exam attempt.

    Prerequisites:
    - All required materials must be completed
    - Exam attempt limit not exceeded
    """
    # Get exam
    exam = db.query(Exam).filter(
        Exam.exam_id == exam_id,
        Exam.is_deleted == 0,
    ).first()

    if not exam:
        return {
            "code": 50001,
            "message": "考试不存在",
        }

    # Check attempt limit
    attempt_count = db.query(ExamAttempt).filter(
        ExamAttempt.exam_id == exam_id,
        ExamAttempt.user_id == current_user.user_id,
        ExamAttempt.status.in_([1, 2]),  # Submitted or auto-submitted
    ).count()

    if attempt_count >= exam.attempt_limit:
        return {
            "code": 50003,
            "message": f"您已使用完所有考试次数（{exam.attempt_limit}次）",
        }

    # Check prerequisite: all materials completed
    materials = db.query(Material).filter(
        Material.project_id == exam.project_id,
        Material.is_deleted == 0,
    ).all()

    for m in materials:
        progress = db.query(WatchProgress).filter(
            WatchProgress.material_id == m.material_id,
            WatchProgress.user_id == current_user.user_id,
            WatchProgress.is_completed == 1,
        ).first()

        if not progress:
            return {
                "code": 50005,
                "message": "请先完成所有必修材料",
            }

    # Check if there's an in-progress attempt
    existing_attempt = db.query(ExamAttempt).filter(
        ExamAttempt.exam_id == exam_id,
        ExamAttempt.user_id == current_user.user_id,
        ExamAttempt.status == 0,  # In progress
    ).first()

    if existing_attempt:
        # Resume existing attempt
        start_time = existing_attempt.start_time
        deadline = start_time + timedelta(minutes=exam.duration_minutes)

        # Check if expired
        if datetime.now() > deadline:
            # Auto submit
            existing_attempt.status = 2
            existing_attempt.submit_time = deadline
            existing_attempt.time_spent = exam.duration_minutes * 60
            db.commit()
            return {
                "code": 50006,
                "message": "考试时间已过期",
            }

        # Return existing attempt
        questions = db.query(Question).filter(
            Question.exam_id == exam_id
        ).order_by(Question.sort_order).all()

        return {
            "code": 0,
            "data": {
                "attempt_id": existing_attempt.attempt_id,
                "start_time": start_time.isoformat(),
                "deadline": deadline.isoformat(),
                "questions": [
                    {
                        "question_id": q.question_id,
                        "question_type": q.question_type,
                        "question_type_text": q.question_type_text,
                        "question_text": q.question_text,
                        "options": json.loads(q.options) if q.options else None,
                        "score": q.score,
                    }
                    for q in questions
                ],
            },
        }

    # Create new attempt
    attempt_id = f"A{uuid.uuid4().hex[:8].upper()}"
    start_time = datetime.now()
    deadline = start_time + timedelta(minutes=exam.duration_minutes)

    attempt = ExamAttempt(
        attempt_id=attempt_id,
        exam_id=exam_id,
        user_id=current_user.user_id,
        start_time=start_time,
        status=0,  # In progress
    )

    db.add(attempt)
    db.commit()

    # Get questions
    questions = db.query(Question).filter(
        Question.exam_id == exam_id
    ).order_by(Question.sort_order).all()

    # Shuffle if needed
    if exam.random_shuffle:
        questions = list(questions)
        random.shuffle(questions)

    return {
        "code": 0,
        "data": {
            "attempt_id": attempt_id,
            "start_time": start_time.isoformat(),
            "deadline": deadline.isoformat(),
            "questions": [
                {
                    "question_id": q.question_id,
                    "question_type": q.question_type,
                    "question_type_text": q.question_type_text,
                    "question_text": q.question_text,
                    "options": json.loads(q.options) if q.options else None,
                    "score": q.score,
                }
                for q in questions
            ],
        },
    }


@router.post("/attempt/{attempt_id}/save")
async def save_attempt(
    attempt_id: str,
    answers: List[dict],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Save exam attempt answers (auto-save).
    """
    # Get attempt
    attempt = db.query(ExamAttempt).filter(
        ExamAttempt.attempt_id == attempt_id,
        ExamAttempt.user_id == current_user.user_id,
    ).first()

    if not attempt:
        return {
            "code": 50001,
            "message": "考试记录不存在",
        }

    if attempt.status != 0:
        return {
            "code": 50002,
            "message": "考试已提交",
        }

    # Update answers
    attempt.answers = json.dumps(answers)
    db.commit()

    return {
        "code": 0,
        "message": "保存成功",
    }


@router.post("/attempt/{attempt_id}/submit")
async def submit_exam(
    attempt_id: str,
    answers: Optional[List[dict]] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Submit exam and calculate score.
    """
    # Get attempt
    attempt = db.query(ExamAttempt).filter(
        ExamAttempt.attempt_id == attempt_id,
        ExamAttempt.user_id == current_user.user_id,
    ).first()

    if not attempt:
        return {
            "code": 50001,
            "message": "考试记录不存在",
        }

    if attempt.status != 0:
        return {
            "code": 50002,
            "message": "考试已提交",
        }

    # Get exam
    exam = db.query(Exam).filter(Exam.exam_id == attempt.exam_id).first()

    # Get questions
    questions = db.query(Question).filter(
        Question.exam_id == attempt.exam_id
    ).all()

    question_map = {q.question_id: q for q in questions}

    # Calculate score
    total_score = 0
    correct_count = 0
    answer_results = []

    submitted_answers = answers or json.loads(attempt.answers or "[]")
    answer_map = {a["question_id"]: a["answer"] for a in submitted_answers}

    for q in questions:
        user_answer = answer_map.get(q.question_id)
        correct = False

        if q.question_type == 1:  # Single choice
            correct = user_answer == q.correct_answer
        elif q.question_type == 2:  # Multiple choice
            correct_set = set(json.loads(q.correct_answer))
            user_set = set(json.loads(user_answer) if user_answer else "[]")
            correct = correct_set == user_set
        elif q.question_type == 3:  # True/False
            correct = user_answer == q.correct_answer

        if correct:
            total_score += q.score
            correct_count += 1

        answer_results.append({
            "question_id": q.question_id,
            "your_answer": user_answer,
            "correct_answer": q.correct_answer if exam.show_answer else None,
            "correct": correct,
        })

    # Calculate time spent
    time_spent = int((datetime.now() - attempt.start_time).total_seconds())

    # Update attempt
    attempt.score = total_score
    attempt.passed = 1 if total_score >= exam.passing_score else 0
    attempt.submit_time = datetime.now()
    attempt.time_spent = time_spent
    attempt.status = 1
    attempt.answers = json.dumps(submitted_answers)

    db.commit()

    return {
        "code": 0,
        "data": {
            "attempt_id": attempt_id,
            "score": total_score,
            "passed": bool(attempt.passed),
            "correct_count": correct_count,
            "total_count": len(questions),
            "submit_time": attempt.submit_time.isoformat(),
            "time_spent": time_spent,
            "answers": answer_results if exam.show_answer else None,
        },
    }


@router.get("/history")
async def get_exam_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get exam history for current user.
    """
    query = db.query(ExamAttempt).filter(
        ExamAttempt.user_id == current_user.user_id,
        ExamAttempt.status.in_([1, 2]),  # Submitted
    )

    total = query.count()
    attempts = query.order_by(ExamAttempt.submit_time.desc()).offset(
        (page - 1) * page_size
    ).limit(page_size).all()

    result = []
    for a in attempts:
        exam = db.query(Exam).filter(Exam.exam_id == a.exam_id).first()
        if exam:
            result.append({
                "attempt_id": a.attempt_id,
                "exam_id": a.exam_id,
                "exam_title": exam.title,
                "start_time": a.start_time.isoformat(),
                "submit_time": a.submit_time.isoformat() if a.submit_time else None,
                "score": a.score,
                "passed": bool(a.passed) if a.passed is not None else None,
                "status": a.status_text,
            })

    return {
        "code": 0,
        "data": {
            "list": result,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
            },
        },
    }