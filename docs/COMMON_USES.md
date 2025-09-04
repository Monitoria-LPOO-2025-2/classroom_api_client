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
uv install

# Setup environment
cp .env.example .env
# Edit .env with your COURSE_ID and credentials

# Authenticate
uv run src/main.py auth login
```

## 🔐 Authentication Setup

### First-Time Authentication
```bash
# Reset any existing credentials
uv run src/main.py auth reset

# Start fresh authentication
uv run src/main.py auth login
```

### Check Current Course
```bash
# Verify your course connection
uv run src/main.py course current

# List all available courses
uv run src/main.py course list
```

## 📥 Downloading Student Submissions

### Use Case 1: Download All Submissions for Grading

**Scenario**: You have an assignment and want to download all student submissions organized by student folders.

```bash
# 1. First, list assignments to get the coursework ID
uv run src/main.py course list-work

# Example output:
# 801325512968: Hello World Assignment
# 923847561234: Final Project

# 2. Download all submissions for the assignment
uv run src/main.py submission download-all 801325512968

# 3. Check the results
ls downloads/
# Gabriel_Borges/
# ├── main.py
# ├── report.pdf
# gabriel_lins/
# └── _no_attachments.txt
```

**Result**: Creates organized folders with all student files ready for review.

### Use Case 2: Download Specific Student's Submission

**Scenario**: You want to download files from one specific student.

```bash
# 1. List all submissions to find the submission ID
uv run src/main.py submission list 801325512968

# 2. Download specific submission
uv run src/main.py submission download 801325512968 Cg4Ix8KMqs4TEIjy45WpFw
```

### Use Case 3: Download with Custom Organization

```bash
# Download to a specific folder
uv run src/main.py submission download-all 801325512968 --download-folder "assignment1_submissions"

# Result: Creates assignment1_submissions/StudentName/ folders
```

## 📊 Grading Workflows

### Use Case 4: Export-Based Grading (Recommended)

**Scenario**: You want to grade assignments but have permission limitations.

```bash
# 1. Export student data to CSV for grading
uv run src/main.py submission export-grades 801325512968

# 2. Open grades.csv in Excel/Google Sheets
# 3. Add grades in the "Grade to Assign" column
# 4. Save the file

# 5. Test import (dry run)
uv run src/main.py submission import-grades 801325512968 grades.csv

# 6. Actually import grades (when permissions allow)
uv run src/main.py submission import-grades 801325512968 grades.csv --no-dry-run
```

### Use Case 5: Direct API Grading (Requires Permissions)

**Scenario**: You have grading permissions and want to grade directly through the API.

```bash
# Test if you have grading permissions
uv run src/main.py submission test-permissions 801325512968

# Single draft grade (not visible to student)
uv run src/main.py submission draft-grade 801325512968 Cg4Ix8KMqs4TEIjy45WpFw 85.5

# Bulk draft grading (same grade for everyone)
uv run src/main.py submission draft-grade-all 801325512968 90.0

# Final grade (visible to student)
uv run src/main.py submission assigned-grade 801325512968 Cg4Ix8KMqs4TEIjy45WpFw 87.5

# Return submission to make grades visible
uv run src/main.py submission return 801325512968 Cg4Ix8KMqs4TEIjy45WpFw
```

### Use Case 6: Review Grades Before Publishing

```bash
# Check all current grades
uv run src/main.py submission show-grades 801325512968

# Example output:
# 👤 Gabriel Borges
#    📊 State: TURNED_IN
#    ✅ Assigned Grade: Not graded
#    📄 Draft Grade: 85.5
```

## 🎓 Course Management

### Use Case 7: Multi-Course Management

**Scenario**: You teach multiple courses and need to switch between them.

```bash
# List all your courses
uv run src/main.py course list

# Get details of a specific course
uv run src/main.py course get 788827935178

# List assignments in a course
uv run src/main.py course list-work --course-id 788827935178
```

### Use Case 8: Assignment Overview

**Scenario**: You want to see all assignments and their submission status.

```bash
# List all assignments
uv run src/main.py course list-work

# For each assignment, check submissions
uv run src/main.py submission list 801325512968

# Get detailed submission info
uv run src/main.py submission info 801325512968 Cg4Ix8KMqs4TEIjy45WpFw
```

## 🔄 Bulk Operations

### Use Case 9: Semester-End Batch Download

**Scenario**: Download all submissions from multiple assignments at semester end.

```bash
# Create a script or run multiple commands
mkdir semester_end_downloads

# Assignment 1
uv run src/main.py submission download-all 801325512968 --download-folder "semester_end_downloads/assignment1"

# Assignment 2  
uv run src/main.py submission download-all 923847561234 --download-folder "semester_end_downloads/assignment2"

# Assignment 3
uv run src/main.py submission download-all 456789123456 --download-folder "semester_end_downloads/final_project"
```

### Use Case 10: Class-Wide Grade Assignment

**Scenario**: Give all students the same grade (e.g., participation points).

```bash
# Export current state
uv run src/main.py submission export-grades 801325512968 --output-file "participation_grades.csv"

# Edit CSV to add same grade for everyone, then import
uv run src/main.py submission import-grades 801325512968 participation_grades.csv --no-dry-run
```

## 💡 Advanced Use Cases

### Use Case 11: Late Submission Tracking

**Scenario**: Identify students who haven't submitted assignments.

```bash
# Export submission data
uv run src/main.py submission export-grades 801325512968

# Check the CSV file for:
# - State: "CREATED" (not submitted)
# - Has Attachments: "No"
```

### Use Case 12: Google Drive File Management

**Scenario**: Download specific files from Google Drive that are submitted.

```bash
# Get file info first
uv run src/main.py drive info 1PDHIMA-BikiW3ZI3Sxr-kJskWeYwSE0p

# Download specific file
uv run src/main.py drive download 1PDHIMA-BikiW3ZI3Sxr-kJskWeYwSE0p "student_code.py"
```

### Use Case 13: Comments and Feedback

**Scenario**: Add feedback comments to student submissions.

```bash
# Add a private comment to a submission
uv run src/main.py submission comment 801325512968 Cg4Ix8KMqs4TEIjy45WpFw "Great work! Consider adding more comments to your code."
```

## 🛠 Workflow Templates

### Complete Assignment Grading Workflow

```bash
# 1. Download all submissions
uv run src/main.py submission download-all {ASSIGNMENT_ID}

# 2. Review files locally
cd downloads/
# ... review student work ...

# 3. Export for grading
uv run src/main.py submission export-grades {ASSIGNMENT_ID}

# 4. Grade in spreadsheet
# Open grades.csv, add grades, save

# 5. Import grades
uv run src/main.py submission import-grades {ASSIGNMENT_ID} grades.csv

# 6. Verify grades
uv run src/main.py submission show-grades {ASSIGNMENT_ID}
```

### Daily Teaching Routine

```bash
# Morning: Check new submissions
uv run src/main.py course list-work
uv run src/main.py submission list {ASSIGNMENT_ID}

# Download new submissions
uv run src/main.py submission download-all {ASSIGNMENT_ID}

# Evening: Grade and provide feedback
uv run src/main.py submission export-grades {ASSIGNMENT_ID}
# ... grade in spreadsheet ...
uv run src/main.py submission import-grades {ASSIGNMENT_ID} grades.csv
```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Permission Denied Errors
```bash
# Test your permissions
uv run src/main.py submission test-permissions {ASSIGNMENT_ID}

# If grading fails, use export method
uv run src/main.py submission export-grades {ASSIGNMENT_ID}
```

#### Authentication Problems
```bash
# Reset and re-authenticate
uv run src/main.py auth reset
uv run src/main.py auth login
```

#### Missing Course ID
```bash
# Find your course
uv run src/main.py course list

# Update .env file with correct COURSE_ID
echo "COURSE_ID=your_course_id" >> .env
```

#### No Submissions Found
```bash
# Verify assignment ID
uv run src/main.py course list-work

# Check if assignment exists
uv run src/main.py submission list {ASSIGNMENT_ID}
```

## 📝 File Organization Tips

### Recommended Directory Structure
```
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
./grade_assignment.sh 801325512968 "hello_world"
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