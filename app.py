from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import jsonschema


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///courses.db'
db = SQLAlchemy(app)

class Courses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    date_start = db.Column(db.Date, nullable=False)
    date_end = db.Column(db.Date, nullable=False)
    lectures_number = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return '<Course %r>' % self.id


def validate_json(json):
    course_schema = {
        "type": "object",
        "properties": {
            "Course Name": {"type": "string"},
            "Date start": {"type": "string"},
            "Date end": {"type": "string"},
            "Number of lectures": {"type": "number"},
        }, "required": ["Course Name", "Date start", "Date end", "Number of lectures"]
    }

    try:
        jsonschema.validate(instance=json, schema=course_schema)
    except jsonschema.exceptions.ValidationError as err:
        print(err)
        return False
    return True


@app.route('/', methods=['GET'])
def index():
    courses = Courses.query.order_by(Courses.id).all()
    res = {"current courses": [{"ID": course.id, "Course Name": course.name} for course in courses]}
    return jsonify(res)


@app.route('/search/<string:text>', methods=['GET'])
def search(text):
    courses = Courses.query.filter_by(name=text).all()
    res = {"current courses": [{"ID": course.id, "Course Name": course.name} for course in courses]}
    return jsonify(res)


@app.route('/datefilter/<int:date1>/<int:date2>', methods=['GET'])
def datefilter(date1, date2):
    date1 = datetime.fromtimestamp(date1)
    date2 = datetime.fromtimestamp(date2)
    courses = db.session.query(Courses).filter(Courses.date_start > date1, Courses.date_end < date2).all()
    res = {"current courses": [{"ID": course.id, "Course Name": course.name} for course in courses]}
    return jsonify(res)


@app.route('/add', methods=['POST'])
def add():
    if request.is_json:
        course_json = request.get_json()

        if validate_json(course_json):
            course_name = course_json['Course Name']
            course_date_start = datetime.strptime(course_json['Date start'], '%d/%m/%Y')
            course_date_end = datetime.strptime(course_json['Date end'], '%d/%m/%Y')
            course_lectures_number = course_json['Number of lectures']

            new_course = Courses(name=course_name, date_start=course_date_start,
                                 date_end=course_date_end, lectures_number=course_lectures_number)

            try:
                db.session.add(new_course)
                db.session.commit()
                return "Course data is stored in the database", 200
            except Exception as error:
                print(error)
                return "There was an issue adding your course", 400
        else:
            return 'JSON has a wrong format. Correct format is { "Course Name": "Text", "Date start": "dd/mm/yyyy",' \
                   '"Date end": "dd/mm/yyyy", "Number of lectures": Int }', 400
    else:
        return "Request was not JSON. Please send JSON", 400


@app.route('/<int:id>', methods=['GET'])
def show_details(id):
    if Courses.query.filter_by(id=id).first():
        course_to_show = Courses.query.get_or_404(id)
        try:
            res = {"Course Name": course_to_show.name, "Date start": course_to_show.date_start,
                   "Date end": course_to_show.date_end, "Number of lectures": course_to_show.lectures_number}
            return jsonify(res), 200
        except:
            return 'There was a problem showing that course', 400
    else:
        return f'There is no course with the ID {id}', 404


@app.route('/delete/<int:id>', methods=['DELETE'])
def delete(id):
    if Courses.query.filter_by(id=id).first():
        course_to_delete = Courses.query.get_or_404(id)
        try:
            db.session.delete(course_to_delete)
            db.session.commit()
            return f"Course {id} deleted from the database", 200
        except:
            return 'There was a problem deleting that task', 400
    else:
        return f'There is no course with the ID {id}', 404


@app.route('/update/<int:id>', methods=['POST'])
def update(id):
    if Courses.query.filter_by(id=id).first():
        course_to_update = Courses.query.get_or_404(id)
        course_json = request.get_json()

        # check if json is in correct format
        if 'Course Name' and 'Date start' and 'Date end' and 'Number of lectures' not in course_json:
            return 'JSON has a wrong format. Correct format is { "Course Name": "Text", "Date start": "dd/mm/yyyy",' \
                   '"Date end": "dd/mm/yyyy", "Number of lectures": Int }', 400

        updated = ""
        if 'Course Name' in course_json:
            course_to_update.name = course_json['Course Name']
            updated += ' /Course Name/'
        if 'Date start' in course_json:
            course_to_update.date_start = datetime.strptime(course_json['Date start'], '%d/%m/%Y')
            updated += ' /Date start/'
        if 'Date end' in course_json:
            course_to_update.date_end = datetime.strptime(course_json['Date end'], '%d/%m/%Y')
            updated += ' /Date end/'
        if 'Number of lectures' in course_json:
            course_to_update.lectures_number = course_json['Number of lectures']
            updated += ' /Number of lectures/'

        try:
            db.session.commit()
            return f"Course data ({updated} ) is updated in the database", 200
        except Exception as error:
            return 'There was an issue updating the course', 400
    else:
        return f'There is no course with the ID {id}', 404


if __name__ == "__main__":
    app.run(debug=True)
