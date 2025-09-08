# Google Classroom API Client - Common Use Cases

This document provides practical examples of how to use the Google Classroom API Client for common educational tasks.

## 📚 Table of Contents

- [Quick Start](#quick-start)
- [Authentication Setup](#authentication-setup)
- [Downloading Student Submissions](#downloading-student-submissions)
- [Grading Workflows](#grading-workflows)
- [Course Management](#course-management)
- [Bulk Operations](#bulk-operations)
- [Troubleshooting](#troubleshooting)

## 🚀 Quick Start

### Prerequisites

1. Python 3.8+ installed
2. Google Cloud Project with Classroom API enabled
3. OAuth 2.0 credentials configured
4. Course ID from Google Classroom

### Basic Setup

```bash
# Clone and setup
git clone <repository>
cd classroom_api_client
uv sync

# Setup environment
cp .env.example .env
# Edit .env with your COURSE_ID and credentials

# Authenticate
gclass auth login
```

## 🔐 Authentication Setup

### First-Time Authentication

```bash
# Reset any existing credentials
gclass auth reset

# Start fresh authentication
gclass auth login
```

### Check Current Course

```bash
# Verify your course connection
gclass course current

# List all available courses
gclass course list
```

## 📥 Downloading Student Submissions

### Use Case 1: Download All Submissions for Grading

**Scenario**: You have an assignment and want to download all student submissions organized by student folders.

```bash
# 1. First, list assignments to get the coursework ID
gclass course list-work

# Example output:
# 123456789012: Hello World Assignment
# 234567890123: Final Project

# 2. Download all submissions for the assignment
gclass submission download-all 123456789012

# 3. Check the results
ls downloads/
# Student_Name/
# ├── main.py
# ├── report.pdf
# Another_Student/
# └── _no_attachments.txt
```

**Result**: Creates organized folders with all student files ready for review.

### Use Case 2: Download Specific Student's Submission

**Scenario**: You want to download files from one specific student.

```bash
# 1. List all submissions to find the submission ID
gclass submission list 123456789012

# 2. Download specific submission
gclass submission download 123456789012 XXXXXXXXXXXXXXXXXXXX
```

### Use Case 3: Download with Custom Organization

```bash
# Download to a specific folder
gclass submission download-all 123456789012 --download-folder "assignment1_submissions"

# Result: Creates assignment1_submissions/StudentName/ folders
```

## 📊 Grading Workflows

### Use Case 4: Export-Based Grading (Recommended)

**Scenario**: You want to grade assignments but have permission limitations.

```bash
# 1. Export student data to CSV for grading
gclass submission export-grades 123456789012

# 2. Open grades.csv in Excel/Google Sheets
# 3. Add grades in the "Grade to Assign" column
# 4. Save the file

# 5. Test import (dry run)
gclass submission import-grades 123456789012 grades.csv

# 6. Actually import grades (when permissions allow)
gclass submission import-grades 123456789012 grades.csv --no-dry-run
```

### Use Case 5: Direct API Grading (Requires Permissions)

**Scenario**: You have grading permissions and want to grade directly through the API.

```bash
# Test if you have grading permissions
gclass submission test-permissions 123456789012

# Single draft grade (not visible to student)
gclass submission draft-grade 123456789012 CgXXXXXXXXXXXXXXXXXXXX 85.5

# Bulk draft grading (same grade for everyone)
gclass submission draft-grade-all 123456789012 90.0

# Final grade (visible to student)
gclass submission assigned-grade 123456789012 CgXXXXXXXXXXXXXXXXXXXX 87.5

# Return submission to make grades visible
gclass submission return 123456789012 CgXXXXXXXXXXXXXXXXXXXX
```

### Use Case 6: Review Grades Before Publishing

```bash
# Check all current grades
gclass submission show-grades 123456789012

# Example output:
# 👤 Student Name
#    📊 State: TURNED_IN
#    ✅ Assigned Grade: Not graded
#    📄 Draft Grade: 85.5
```

## 🎓 Course Management

### Use Case 7: Multi-Course Management

**Scenario**: You teach multiple courses and need to switch between them.

```bash
# List all your courses
gclass course list

# Get details of a specific course
gclass course get 345678901234

# List assignments in a course
gclass course list-work --course-id 345678901234
```

### Use Case 8: Assignment Overview

**Scenario**: You want to see all assignments and their submission status.

```bash
# List all assignments
gclass course list-work

# For each assignment, check submissions
gclass submission list 123456789012

# Get detailed submission info
gclass submission info 123456789012 CgXXXXXXXXXXXXXXXXXXXX
```

## 🔄 Bulk Operations

### Use Case 9: Semester-End Batch Download

**Scenario**: Download all submissions from multiple assignments at semester end.

```bash
# Create a script or run multiple commands
mkdir semester_end_downloads

# Assignment 1
gclass submission download-all 123456789012 --download-folder "semester_end_downloads/assignment1"

# Assignment 2  
gclass submission download-all 234567890123 --download-folder "semester_end_downloads/assignment2"

# Assignment 3
gclass submission download-all 345678901234 --download-folder "semester_end_downloads/final_project"
```

### Use Case 10: Class-Wide Grade Assignment

**Scenario**: Give all students the same grade (e.g., participation points).

```bash
# Export current state
gclass submission export-grades 123456789012 --output-file "participation_grades.csv"

# Edit CSV to add same grade for everyone, then import
gclass submission import-grades 123456789012 participation_grades.csv --no-dry-run
```

### Use Case 11: Comprehensive Submissions Export

**Scenario**: Export all submission data for analysis, reporting, or archival purposes.

```bash
# Export all submissions from a specific assignment
gclass submission export-submissions-csv --coursework-id 123456789012 --output submissions_assignment1.csv

# Export all submissions from all assignments in a course (by course ID)
gclass submission export-submissions-csv --course-id 567890123456 --output all_course_submissions.csv

# Export using course/assignment names instead of IDs
gclass submission export-submissions-csv --course-name "Intro to Programming" --work-name "Final Project" --output final_project_submissions.csv

# Export without attachment details for faster processing
gclass submission export-submissions-csv --course-name "Data Science" --no-attachments --output ds_submissions_minimal.csv
```

**The CSV export includes:**

- Course and assignment information
- Student details (name, email, user ID)  
- Submission metadata (ID, state, timestamps)
- Grading information (assigned grade, draft grade)
- Attachment details (count, file names, Drive IDs, links)
- Late submission indicators

**Use cases for the comprehensive export:**

- **Academic Analytics**: Analyze submission patterns and student engagement
- **Compliance & Archival**: Keep records for institutional requirements
- **Cross-Platform Integration**: Import data into other educational tools
- **Progress Tracking**: Monitor class progress across multiple assignments
- **Research Data**: Use submission timing and patterns for educational research

## 💡 Advanced Use Cases

### Use Case 11: Late Submission Tracking

**Scenario**: Identify students who haven't submitted assignments.

```bash
# Export submission data
gclass submission export-grades 123456789012

# Check the CSV file for:
# - State: "CREATED" (not submitted)
# - Has Attachments: "No"
```

### Use Case 12: Google Drive File Management

**Scenario**: Download specific files from Google Drive that are submitted.

```bash
# Get file info first
gclass drive info 1XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Download specific file
gclass drive download 1XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX "student_code.py"
```

### Use Case 13: Comments and Feedback

**Scenario**: Add feedback comments to student submissions.

```bash
# Add a private comment to a submission
gclass submission comment 123456789012 CgXXXXXXXXXXXXXXXXXXXX "Great work! Consider adding more comments to your code."
```

## 🛠 Workflow Templates

### Complete Assignment Grading Workflow

```bash
# 1. Download all submissions
gclass submission download-all {ASSIGNMENT_ID}

# 2. Review files locally
cd downloads/
# ... review student work ...

# 3. Export for grading
gclass submission export-grades {ASSIGNMENT_ID}

# 4. Grade in spreadsheet
# Open grades.csv, add grades, save

# 5. Import grades
gclass submission import-grades {ASSIGNMENT_ID} grades.csv

# 6. Verify grades
gclass submission show-grades {ASSIGNMENT_ID}
```

### Daily Teaching Routine

```bash
# Morning: Check new submissions
gclass course list-work
gclass submission list {ASSIGNMENT_ID}

# Download new submissions
gclass submission download-all {ASSIGNMENT_ID}

# Evening: Grade and provide feedback
gclass submission export-grades {ASSIGNMENT_ID}
# ... grade in spreadsheet ...
gclass submission import-grades {ASSIGNMENT_ID} grades.csv
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Permission Denied Errors

```bash
# Test your permissions
gclass submission test-permissions {ASSIGNMENT_ID}

# If grading fails, use export method
gclass submission export-grades {ASSIGNMENT_ID}
```

#### Authentication Problems

```bash
# Reset and re-authenticate
gclass auth reset
gclass auth login
```

#### Missing Course ID

```bash
# Find your course
gclass course list

# Update .env file with correct COURSE_ID
echo "COURSE_ID=your_course_id" >> .env
```

#### No Submissions Found

```bash
# Verify assignment ID
gclass course list-work

# Check if assignment exists
gclass submission list {ASSIGNMENT_ID}
```

## 📝 File Organization Tips

### Recommended Directory Structure

```text
course_files/
├── assignments/
│   ├── assignment1/
│   │   ├── downloads/           # Student submissions
│   │   ├── grades.csv          # Grading spreadsheet
│   │   └── rubric.pdf          # Grading rubric
│   ├── assignment2/
│   └── final_project/
├── class_roster/
│   └── students.csv            # Exported student info
└── gradebook/
    └── semester_grades.xlsx    # Master gradebook
```

### Automation Scripts

Create a bash script for repeated tasks:

```bash
#!/bin/bash
# grade_assignment.sh

ASSIGNMENT_ID=$1
ASSIGNMENT_NAME=$2

echo "Processing $ASSIGNMENT_NAME (ID: $ASSIGNMENT_ID)"

# Create folder
mkdir -p "assignments/$ASSIGNMENT_NAME"
cd "assignments/$ASSIGNMENT_NAME"

# Download submissions
uv run ../../src/main.py submission download-all $ASSIGNMENT_ID

# Export for grading
uv run ../../src/main.py submission export-grades $ASSIGNMENT_ID

echo "Files ready for grading in assignments/$ASSIGNMENT_NAME"
```

Usage:

```bash
chmod +x grade_assignment.sh
./grade_assignment.sh 123456789012 "hello_world"
```

## 🎯 Best Practices

1. **Always backup**: Export grades before making changes
2. **Use dry-run**: Test imports before applying
3. **Organize files**: Use consistent folder structures
4. **Document workflow**: Keep notes on your grading process
5. **Test permissions**: Check capabilities before bulk operations
6. **Version control**: Keep track of grade file versions

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify your Google Cloud Project permissions
3. Ensure you have the latest version of the CLI
4. Check the assignment ID is correct
5. Verify your course access permissions

Remember: The export-import workflow works even when direct API grading doesn't!
