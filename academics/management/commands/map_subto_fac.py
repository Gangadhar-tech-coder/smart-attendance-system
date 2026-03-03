# academics/management/commands/map_subjects_to_faculty.py
"""
Management command to map existing subjects to faculty and create allocations
Usage: python manage.py map_subjects_to_faculty
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from academics.models import Subject, SubjectAllocation, Semester, Course
from profiles.models import FacultyProfile
from academics.models import Subject as AccountsSubject

User = get_user_model()


class Command(BaseCommand):
    help = 'Map existing subjects to faculty and create subject allocations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--migrate-accounts-subjects',
            action='store_true',
            help='Migrate subjects from accounts.Subject to academics.Subject',
        )
        
        parser.add_argument(
            '--auto-allocate',
            action='store_true',
            help='Automatically create allocations for all subjects',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting subject mapping...'))
        
        # Step 1: Migrate subjects from accounts app to academics app
        if options['migrate_accounts_subjects']:
            self.stdout.write('\n' + '='*60)
            self.stdout.write('Step 1: Migrating Subjects from accounts to academics')
            self.stdout.write('='*60)
            
            from academics.models import Department
            
            accounts_subjects = AccountsSubject.objects.all()
            migrated_count = 0
            
            for acc_subject in accounts_subjects:
                # Get or create department
                dept_code = None
                if acc_subject.staff.department:
                    dept_code = acc_subject.staff.department
                else:
                    # Default to first department or create one
                    dept_code = 'CSE'
                
                dept, _ = Department.objects.get_or_create(
                    code=dept_code,
                    defaults={'name': f'{dept_code} Department', 'is_active': True}
                )
                
                # Create/update academic subject
                acad_subject, created = Subject.objects.get_or_create(
                    subject_code=acc_subject.code,
                    defaults={
                        'name': acc_subject.name,
                        'department': dept,
                        'credits': 3,  # Default credits
                        'is_active': True
                    }
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ Migrated: {acad_subject.subject_code} - {acad_subject.name}'
                    ))
                    migrated_count += 1
                else:
                    self.stdout.write(self.style.WARNING(
                        f'○ Already exists: {acad_subject.subject_code}'
                    ))
            
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Migrated {migrated_count} subjects'
            ))
        
        # Step 2: Auto-allocate subjects to faculty
        if options['auto_allocate']:
            self.stdout.write('\n' + '='*60)
            self.stdout.write('Step 2: Auto-allocating Subjects to Faculty')
            self.stdout.write('='*60)
            
            # Get current semester
            from academics.models import AcademicYear
            current_ay = AcademicYear.objects.filter(is_current=True).first()
            
            if not current_ay:
                self.stdout.write(self.style.ERROR(
                    '✗ No current academic year found. Please create one first.'
                ))
                return
            
            # Get first semester of current year
            semester = Semester.objects.filter(
                academic_year=current_ay,
                number=1
            ).first()
            
            if not semester:
                self.stdout.write(self.style.ERROR(
                    '✗ No semester found. Creating semesters...'
                ))
                # Create semesters
                from datetime import timedelta
                year_duration = (current_ay.end_date - current_ay.start_date).days
                semester_duration = year_duration // 8
                
                for sem_num in range(1, 9):
                    start_date = current_ay.start_date + timedelta(days=(sem_num - 1) * semester_duration)
                    end_date = current_ay.start_date + timedelta(days=sem_num * semester_duration - 1)
                    if sem_num == 8:
                        end_date = current_ay.end_date
                    
                    Semester.objects.get_or_create(
                        academic_year=current_ay,
                        number=sem_num,
                        defaults={
                            'start_date': start_date,
                            'end_date': end_date,
                            'is_active': sem_num in [1, 2]
                        }
                    )
                
                semester = Semester.objects.filter(academic_year=current_ay, number=1).first()
            
            # Now allocate subjects
            allocated_count = 0
            
            # Method 1: Allocate based on accounts.Subject staff assignment
            accounts_subjects = AccountsSubject.objects.select_related('staff')
            
            for acc_subject in accounts_subjects:
                # Find corresponding academic subject
                acad_subject = Subject.objects.filter(subject_code=acc_subject.code).first()
                
                if not acad_subject:
                    self.stdout.write(self.style.WARNING(
                        f'⚠️ Subject {acc_subject.code} not found in academics. Skipping.'
                    ))
                    continue
                
                # Get faculty profile for staff
                try:
                    faculty = FacultyProfile.objects.get(user=acc_subject.staff)
                except FacultyProfile.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f'⚠️ No faculty profile for {acc_subject.staff.username}. Creating...'
                    ))
                    # Create faculty profile
                    from academics.models import Department
                    dept = Department.objects.first()
                    
                    # Generate staff_id
                    last_faculty = FacultyProfile.objects.order_by('-id').first()
                    if last_faculty:
                        last_id = int(last_faculty.staff_id.split('-')[1])
                        staff_id = f'FAC-{last_id + 1:04d}'
                    else:
                        staff_id = f'FAC-0001'
                    
                    faculty = FacultyProfile.objects.create(
                        user=acc_subject.staff,
                        staff_id=staff_id,
                        department=dept,
                        designation='Faculty Member'
                    )
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ Created faculty profile: {staff_id}'
                    ))
                
                # Create allocation
                allocation, created = SubjectAllocation.objects.get_or_create(
                    faculty=faculty,
                    subject=acad_subject,
                    semester=semester,
                    defaults={
                        'is_active': True,
                        'notes': 'Auto-allocated during migration'
                    }
                )
                
                if created:
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ Allocated: {acad_subject.name} → {faculty.user.get_full_name()}'
                    ))
                    allocated_count += 1
                else:
                    self.stdout.write(self.style.WARNING(
                        f'○ Already allocated: {acad_subject.name} → {faculty.user.get_full_name()}'
                    ))
            
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Created {allocated_count} allocations'
            ))
        
        # Step 3: Show summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('MAPPING COMPLETE!'))
        self.stdout.write('='*60)
        
        # Statistics
        self.stdout.write('\nCurrent Statistics:')
        self.stdout.write(f'  Academic Subjects: {Subject.objects.count()}')
        self.stdout.write(f'  Accounts Subjects: {AccountsSubject.objects.count()}')
        self.stdout.write(f'  Faculty Profiles: {FacultyProfile.objects.count()}')
        self.stdout.write(f'  Subject Allocations: {SubjectAllocation.objects.count()}')
        self.stdout.write(f'  Courses: {Course.objects.count()}')
        
        # Show allocations
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Current Allocations:')
        self.stdout.write('='*60)
        
        allocations = SubjectAllocation.objects.select_related(
            'faculty__user', 'subject', 'semester'
        ).all()
        
        if allocations.exists():
            for alloc in allocations:
                self.stdout.write(
                    f'  • {alloc.subject.name} ({alloc.subject.subject_code}) → '
                    f'{alloc.faculty.user.get_full_name()} '
                    f'[{alloc.semester}]'
                )
        else:
            self.stdout.write(self.style.WARNING('  No allocations found.'))
        
        # Show available subjects without allocation
        self.stdout.write('\n' + '='*60)
        self.stdout.write('Subjects WITHOUT Allocation:')
        self.stdout.write('='*60)
        
        allocated_subject_ids = SubjectAllocation.objects.values_list('subject_id', flat=True)
        unallocated = Subject.objects.exclude(id__in=allocated_subject_ids)
        
        if unallocated.exists():
            for subject in unallocated:
                self.stdout.write(self.style.WARNING(
                    f'  ⚠️ {subject.name} ({subject.subject_code}) - Not allocated'
                ))
            
            self.stdout.write('\n' + self.style.WARNING(
                f'Total unallocated subjects: {unallocated.count()}'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('  ✓ All subjects are allocated!'))
        
        # Next steps
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('Next Steps:'))
        self.stdout.write('='*60)
        self.stdout.write('1. Review allocations in admin panel')
        self.stdout.write('2. Create courses for allocated subjects')
        self.stdout.write('3. Enroll students in courses')
        self.stdout.write('4. Start creating attendance sessions')
        
        self.stdout.write('\nUseful commands:')
        self.stdout.write('  python manage.py setup_academic_structure --sample-data')
        self.stdout.write('  python manage.py shell')