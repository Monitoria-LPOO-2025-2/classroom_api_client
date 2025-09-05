# New Grading Commands

This document describes the new grading commands added to the CLI for pushing draft grades and grades for student submissions.

## New Commands

### 1. `submission grade-all`
Assign the same final grade to all submissions in an assignment.

```bash
python main.py submission grade-all COURSEWORK_ID GRADE [--course-id COURSE_ID]
```

**Example:**
```bash
python main.py submission grade-all hw123 85.0
```

**Features:**
- Sets both draft and final grades for all students
- Shows progress for each student
- Handles permission errors gracefully
- Provides summary statistics

### 2. `submission push-draft-grades`
Push all existing draft grades to become final grades (make them visible to students).

```bash
python main.py submission push-draft-grades COURSEWORK_ID [--course-id COURSE_ID]
```

**Example:**
```bash
python main.py submission push-draft-grades hw123
```

**Features:**
- Converts draft grades to final grades
- Only processes submissions that have draft grades
- Shows which students have no draft grades
- Preserves existing final grades if no draft grade exists

### 3. `submission push-grades-from-file`
Push grades from CSV file to student submissions (enhanced import functionality).

```bash
python main.py submission push-grades-from-file COURSEWORK_ID GRADES_FILE [--course-id COURSE_ID] [--grade-type TYPE]
```

**Example:**
```bash
python main.py submission push-grades-from-file hw123 grades.csv --grade-type final
```

**Parameters:**
- `--grade-type`: `draft`, `final`, or `both` (default: `final`)

**CSV Format:**
The CSV file should have these columns:
- `Student Name`: Student's display name
- `Submission ID`: The submission ID from Google Classroom
- `Grade to Assign` or `Grade`: The numeric grade to assign

**Features:**
- Supports both metadata-style and simple CSV formats
- Flexible column names (`Grade to Assign` or `Grade`)
- Handles different grade types (draft, final, both)
- Validates grade values
- Shows detailed progress and error reporting

### 4. `submission push-grades-bulk`
Interactive bulk grade pusher - assign grades to multiple students at once.

```bash
python main.py submission push-grades-bulk COURSEWORK_ID [--course-id COURSE_ID] [--grade-type TYPE]
```

**Example:**
```bash
python main.py submission push-grades-bulk hw123 --grade-type draft
```

**Features:**
- Interactive command-line interface
- Shows all students with current grades
- Multiple input formats:
  - Single student: `1:85`
  - Multiple students: `1:85 2:90 3:78`
  - Range: `1-5:85` (assigns 85 to students 1-5)
  - All students: `all:85`
- Real-time confirmation before applying grades
- Updates display with new grades

## Workflow Examples

### Typical Grading Workflow

1. **Export grades for review:**
   ```bash
   python main.py submission export-grades hw123
   ```

2. **Grade all submissions with a base grade:**
   ```bash
   python main.py submission grade-all hw123 75 --grade-type draft
   ```

3. **Make individual adjustments:**
   ```bash
   python main.py submission push-grades-bulk hw123 --grade-type draft
   ```

4. **Push draft grades to final:**
   ```bash
   python main.py submission push-draft-grades hw123
   ```

5. **Return submissions to students:**
   ```bash
   python main.py submission return hw123
   ```

### Bulk Grading from File

1. **Export current grades:**
   ```bash
   python main.py submission export-grades hw123 --output-file grades.csv
   ```

2. **Edit grades.csv in Excel/Google Sheets**

3. **Push updated grades:**
   ```bash
   python main.py submission push-grades-from-file hw123 grades.csv --grade-type final
   ```

## Error Handling

All commands include comprehensive error handling:
- **Permission errors**: Suggests using `export-grades` for manual grading
- **Invalid grades**: Validates numeric values
- **Missing students**: Reports students that couldn't be processed
- **Network issues**: Provides helpful error messages

## Compatibility

These new commands are fully compatible with existing grading commands:
- `submission grade` - Individual grading
- `submission draft-grade` - Individual draft grading  
- `submission assigned-grade` - Individual final grading
- `submission show-grades` - View current grades
- `submission export-grades` - Export to CSV
- `submission import-grades` - Legacy import (now use `push-grades-from-file`)

The new "push" commands provide more intuitive workflows for common grading tasks while maintaining backward compatibility with the existing API.