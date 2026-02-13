# academics/management/commands/setup_academic_structure.py
"""
Management command to set up complete academic structure with interconnections
Usage: python manage.py setup_academic_structure
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from academics.models import (
    Department, AcademicYear, Semester, Subject, 
    Course, SubjectAllocation, CourseEnrollment
)
from profiles.models import FacultyProfile, StudentProfile
from datetime import date, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Set up complete academic structure with all interconnections'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sample-data',
            action='store_true',
            help='Create sample data for testing',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting academic structure setup...'))
        
        # Step 1: Create Academic Year
        self.stdout.write('\n' + '='*50)
        self.stdout.write('Step 1: Creating Academic Year')
        self.stdout.write('='*50)
        
        current_year = date.today().year
        ay, created = AcademicYear.objects.get_or_create(
            name=f'{current_year}-{str(current_year + 1)[-2:]}',
            defaults={
                'start_date': date(current_year, 8, 1),
                'end_date': date(current_year + 1, 7, 31),
                'is_active': True,
                'is_current': True
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✓ Created Academic Year: {ay.name}'))
        else:
            self.stdout.write(self.style.WARNING(f'○ Academic Year already exists: {ay.name}'))
        
        # Step 2: Create Semesters for this Academic Year
        self.stdout.write('\n' + '='*50)
        self.stdout.write('Step 2: Creating Semesters')
        self.stdout.write('='*50)
        
        semester_dates = [
            (1, date(current_year, 8, 1), date(current_year, 12, 31)),
            (2, date(current_year + 1, 1, 1), date(current_year + 1, 5, 31)),
            (3, date(current_year, 8, 1), date(current_year, 12, 31)),
            (4, date(current_year + 1, 1, 1), date(current_year + 1, 5, 31)),
            (5, date(current_year, 8, 1), date(current_year, 12, 31)),
            (6, date(current_year + 1, 1, 1), date(current_year + 1, 5, 31)),
            (7, date(current_year, 8, 1), date(current_year, 12, 31)),
            (8, date(current_year + 1, 1, 1), date(current_year + 1, 5, 31)),
        ]
        
        semesters = []
        for num, start, end in semester_dates:
            sem, created = Semester.objects.get_or_create(
                academic_year=ay,
                number=num,
                defaults={
                    'start_date': start,
                    'end_date': end,
                    'is_active': num in [1, 2]  # Only first year semesters active by default
                }
            )
            semesters.append(sem)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created {sem}'))
            else:
                self.stdout.write(self.style.WARNING(f'○ {sem} already exists'))
        
        # Step 3: Create Departments
        self.stdout.write('\n' + '='*50)
        self.stdout.write('Step 3: Creating Departments')
        self.stdout.write('='*50)
        
        departments_data = [
            {'name': 'Computer Science and Engineering', 'code': 'CSE'},
            {'name': 'Electronics and Communication Engineering', 'code': 'ECE'},
            {'name': 'Mechanical Engineering', 'code': 'MECH'},
            {'name': 'Civil Engineering', 'code': 'CIVIL'},
            {'name': 'Electrical Engineering', 'code': 'EEE'},
        ]
        
        departments = []
        for dept_data in departments_data:
            dept, created = Department.objects.get_or_create(
                code=dept_data['code'],
                defaults={
                    'name': dept_data['name'],
                    'is_active': True
                }
            )
            departments.append(dept)
            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created Department: {dept.code} - {dept.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'○ Department already exists: {dept.code}'))
        
        # Step 4: Create Sample Users and Profiles (if --sample-data flag)
        if options['sample_data']:
            self.stdout.write('\n' + '='*50)
            self.stdout.write('Step 4: Creating Sample Users & Profiles')
            self.stdout.write('='*50)
            
            # Create HOD for CSE
            hod_user, created = User.objects.get_or_create(
                username='hod_cse',
                defaults={
                    'email': 'hod.cse@college.edu',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'user_type': 'hod',
                    'department': 'CSE'
                }
            )
            if created:
                hod_user.set_password('password123')
                hod_user.save()
                self.stdout.write(self.style.SUCCESS(f'✓ Created HOD: {hod_user.username}'))
            
            # Assign HOD to department
            cse_dept = Department.objects.get(code='CSE')
            cse_dept.hod = hod_user
            cse_dept.save()
            self.stdout.write(self.style.SUCCESS(f'✓ Assigned {hod_user.username} as HOD of CSE'))
            
            # Create Faculty
            faculty_data = [
                {'username': 'faculty_cse1', 'dept': 'CSE', 'first_name': 'Alice', 'last_name': 'Smith'},
                {'username': 'faculty_cse2', 'dept': 'CSE', 'first_name': 'Bob', 'last_name': 'Johnson'},
                {'username': 'faculty_ece1', 'dept': 'ECE', 'first_name': 'Charlie', 'last_name': 'Williams'},
            ]
            
            faculties = []
            for fac_data in faculty_data:
                user, created = User.objects.get_or_create(
                    username=fac_data['username'],
                    defaults={
                        'email': f"{fac_data['username']}@college.edu",
                        'first_name': fac_data['first_name'],
                        'last_name': fac_data['last_name'],
                        'user_type': 'staff',
                        'department': fac_data['dept']
                    }
                )
                if created:
                    user.set_password('password123')
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f'✓ Created Faculty: {user.username}'))
                    
                    # Profile is auto-created by signal
                    if hasattr(user, 'faculty_profile'):
                        faculties.append(user.faculty_profile)
            
            # Create Students
            student_data = [
                {'username': 'student_001', 'dept': 'CSE', 'year': 1, 'section': 'A'},
                {'username': 'student_002', 'dept': 'CSE', 'year': 1, 'section': 'A'},
                {'username': 'student_003', 'dept': 'CSE', 'year': 1, 'section': 'B'},
                {'username': 'student_004', 'dept': 'ECE', 'year': 1, 'section': 'A'},
                {'username': 'student_005', 'dept': 'ECE', 'year': 2, 'section': 'A'},
            ]
            
            students = []
            for std_data in student_data:
                user, created = User.objects.get_or_create(
                    username=std_data['username'],
                    defaults={
                        'email': f"{std_data['username']}@student.college.edu",
                        'first_name': std_data['username'].replace('_', ' ').title(),
                        'last_name': 'Student',
                        'user_type': 'student',
                        'student_id': f"2024{std_data['dept']}{std_data['year']}{std_data['section']}{std_data['username'][-3:]}",
                        'department': std_data['dept']
                    }
                )
                if created:
                    user.set_password('password123')
                    user.save()
                    self.stdout.write(self.style.SUCCESS(f'✓ Created Student: {user.username}'))
                    
                    # Update profile with year and section
                    if hasattr(user, 'student_profile'):
                        profile = user.student_profile
                        profile.year = std_data['year']
                        profile.section = std_data['section']
                        profile.save()
                        students.append(profile)
            
            # Step 5: Create Subjects
            self.stdout.write('\n' + '='*50)
            self.stdout.write('Step 5: Creating Subjects')
            self.stdout.write('='*50)
            
            subjects_data = [
                {'code': 'CSE101', 'name': 'Programming in C', 'dept': 'CSE', 'credits': 4},
                {'code': 'CSE102', 'name': 'Data Structures', 'dept': 'CSE', 'credits': 4},
                {'code': 'CSE201', 'name': 'Database Management', 'dept': 'CSE', 'credits': 3},
                {'code': 'ECE101', 'name': 'Circuit Theory', 'dept': 'ECE', 'credits': 4},
            ]
            
            subjects = []
            for sub_data in subjects_data:
                dept = Department.objects.get(code=sub_data['dept'])
                subject, created = Subject.objects.get_or_create(
                    subject_code=sub_data['code'],
                    defaults={
                        'name': sub_data['name'],
                        'department': dept,
                        'credits': sub_data['credits'],
                        'is_active': True
                    }
                )
                subjects.append(subject)
                if created:
                    self.stdout.write(self.style.SUCCESS(f'✓ Created Subject: {subject.subject_code} - {subject.name}'))
            
            # Step 6: Create Courses (specific to year/section)
            self.stdout.write('\n' + '='*50)
            self.stdout.write('Step 6: Creating Courses')
            self.stdout.write('='*50)
            
            courses_data = [
                {'subject_code': 'CSE101', 'year': 1, 'section': 'A'},
                {'subject_code': 'CSE101', 'year': 1, 'section': 'B'},
                {'subject_code': 'CSE102', 'year': 1, 'section': 'A'},
                {'subject_code': 'CSE201', 'year': 2, 'section': 'A'},
                {'subject_code': 'ECE101', 'year': 1, 'section': 'A'},
                {'subject_code': 'ECE101', 'year': 2, 'section': 'A'},
            ]
            
            courses = []
            for course_data in courses_data:
                subject = Subject.objects.get(subject_code=course_data['subject_code'])
                course, created = Course.objects.get_or_create(
                    code=subject.subject_code,
                    academic_year=ay,
                    section=course_data['section'],
                    defaults={
                        'name': subject.name,
                        'subject': subject,
                        'department': subject.department,
                        'year': course_data['year'],
                        'credits': subject.credits,
                        'is_active': True
                    }
                )
                courses.append(course)
                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ Created Course: {course.code} - Year {course.year} Section {course.section}'
                    ))
            
            # Step 7: Allocate Subjects to Faculty
            self.stdout.write('\n' + '='*50)
            self.stdout.write('Step 7: Allocating Subjects to Faculty')
            self.stdout.write('='*50)
            
            # Get faculty
            faculty_cse1 = FacultyProfile.objects.filter(user__username='faculty_cse1').first()
            faculty_cse2 = FacultyProfile.objects.filter(user__username='faculty_cse2').first()
            
            allocations_data = [
                {'faculty': faculty_cse1, 'subject_code': 'CSE101', 'semester': 1},
                {'faculty': faculty_cse2, 'subject_code': 'CSE102', 'semester': 1},
            ]
            
            for alloc_data in allocations_data:
                if alloc_data['faculty']:
                    subject = Subject.objects.get(subject_code=alloc_data['subject_code'])
                    semester = semesters[alloc_data['semester'] - 1]
                    
                    allocation, created = SubjectAllocation.objects.get_or_create(
                        faculty=alloc_data['faculty'],
                        subject=subject,
                        semester=semester,
                        defaults={
                            'is_active': True,
                            'assigned_by': hod_user
                        }
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(
                            f'✓ Allocated {subject.name} to {alloc_data["faculty"].user.get_full_name()}'
                        ))
            
            # Step 8: Enroll Students in Courses
            self.stdout.write('\n' + '='*50)
            self.stdout.write('Step 8: Enrolling Students in Courses')
            self.stdout.write('='*50)
            
            # Enroll CSE Year 1 Section A students
            cse_1a_students = StudentProfile.objects.filter(
                department__code='CSE',
                year=1,
                section='A'
            )
            
            cse_1a_courses = Course.objects.filter(
                department__code='CSE',
                year=1,
                section='A'
            )
            
            for student in cse_1a_students:
                for course in cse_1a_courses:
                    enrollment, created = CourseEnrollment.objects.get_or_create(
                        student=student,
                        course=course,
                        defaults={'is_active': True}
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(
                            f'✓ Enrolled {student.roll_number} in {course.code}'
                        ))
            
            # Enroll ECE Year 1 Section A students
            ece_1a_students = StudentProfile.objects.filter(
                department__code='ECE',
                year=1,
                section='A'
            )
            
            ece_1a_courses = Course.objects.filter(
                department__code='ECE',
                year=1,
                section='A'
            )
            
            for student in ece_1a_students:
                for course in ece_1a_courses:
                    enrollment, created = CourseEnrollment.objects.get_or_create(
                        student=student,
                        course=course,
                        defaults={'is_active': True}
                    )
                    if created:
                        self.stdout.write(self.style.SUCCESS(
                            f'✓ Enrolled {student.roll_number} in {course.code}'
                        ))
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('SETUP COMPLETE!'))
        self.stdout.write('='*50)
        self.stdout.write(f'Academic Years: {AcademicYear.objects.count()}')
        self.stdout.write(f'Semesters: {Semester.objects.count()}')
        self.stdout.write(f'Departments: {Department.objects.count()}')
        self.stdout.write(f'Subjects: {Subject.objects.count()}')
        self.stdout.write(f'Courses: {Course.objects.count()}')
        self.stdout.write(f'Faculty: {FacultyProfile.objects.count()}')
        self.stdout.write(f'Students: {StudentProfile.objects.count()}')
        self.stdout.write(f'Allocations: {SubjectAllocation.objects.count()}')
        self.stdout.write(f'Enrollments: {CourseEnrollment.objects.count()}')
        
        if options['sample_data']:
            self.stdout.write('\n' + self.style.WARNING('Sample login credentials:'))
            self.stdout.write('HOD: hod_cse / password123')
            self.stdout.write('Faculty: faculty_cse1 / password123')
            self.stdout.write('Student: student_001 / password123')