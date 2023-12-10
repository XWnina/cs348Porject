from flask import Flask, request, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:123456@34.42.170.42/348project'
db = SQLAlchemy(app)


class Account(db.Model):
    __tablename__ = 'account'
    s_id = db.Column(db.String(80), primary_key=True)
    password = db.Column(db.String(80))


class Courses(db.Model):
    __tablename__ = 'courses'
    course_name = db.Column(db.String(255), primary_key=True)
    day1 = db.Column(db.String(255))
    day2 = db.Column(db.String(255))
    day3 = db.Column(db.String(255))
    day4 = db.Column(db.String(255))
    day5 = db.Column(db.String(255))
    time = db.Column(db.String(255))


class StudentList(db.Model):
    __tablename__ = 'studentList'
    course_name = db.Column(db.String(255), primary_key=True)
    s_id = db.Column(db.String(255), db.ForeignKey('account.s_id'), primary_key=True)


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form['s_id']
        password = request.form['password']

        sql = text("SELECT * FROM account WHERE s_id = :s_id AND password = :password")
        result = db.session.execute(sql, {'s_id': user_id, 'password': password}).fetchone()

        if result:
            return redirect(url_for('courses', s_id=user_id))
        else:
            return 'Invalid s_id or password, please retry.'

    return render_template('login.html')


@app.route('/courses/<s_id>', methods=['GET', 'POST'])
def courses(s_id):
    course_names = [course.course_name for course in StudentList.query.filter_by(s_id=s_id).all()]
    queried_course = None

    if request.method == 'POST' and 'query_course_name' in request.form:
        course_name = request.form['query_course_name']
        course_data = Courses.query.filter_by(course_name=course_name).first()
        if course_data:
            days = [day for day, value in zip(["Mon", "Tue", "Wed", "Thu", "Fri"],
                                              [course_data.day1, course_data.day2, course_data.day3, course_data.day4,
                                               course_data.day5]) if value == '1']
            days_str = ", ".join(days)
            queried_course = {"course_name": course_name, "days": days_str, "time": course_data.time}
        else:
            return "No info related to this course."

    return render_template('courses.html', course_names=course_names, s_id=s_id, queried_course=queried_course)


@app.route('/delete_course/<s_id>/<course_name>')
def delete_course(s_id, course_name):
    # Check if the course exists
    existing_course = StudentList.query.filter_by(s_id=s_id, course_name=course_name).first()
    if not existing_course:
        return "This course might been deleted already, please refresh the page. "

    try:
        # Attempt to delete the course
        sql = text("DELETE FROM studentList WHERE s_id = :s_id AND course_name = :course_name")
        db.session.execute(sql, {'s_id': s_id, 'course_name': course_name})
        db.session.commit()
        return redirect(url_for('courses', s_id=s_id))
    except IntegrityError:
        # Handle the case where the deletion fails
        db.session.rollback()
        return "Deletion fails."


@app.route('/add_course/<s_id>', methods=['POST'])
def add_course(s_id):
    course_name = request.form['new_course']

    # Check if the course is already added
    existing_course = StudentList.query.filter_by(s_id=s_id, course_name=course_name).first()
    if existing_course:
        return "This course has already been added."

    try:
        # Attempt to insert the new course
        sql = text("INSERT INTO studentList (course_name, s_id) VALUES (:course_name, :s_id)")
        db.session.execute(sql, {'course_name': course_name, 's_id': s_id})
        db.session.commit()
        return redirect(url_for('courses', s_id=s_id))
    except IntegrityError:
        # Handle the case where the insertion fails due to a unique constraint violation
        db.session.rollback()
        return "This course has already been added.。"


if __name__ == '__main__':
    app.run(port=5008, debug=True)
