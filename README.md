# Database Development Assistant (DDA) Tool Suite

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)
![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-orange)
![License](https://img.shields.io/badge/license-MIT-green)
![Status](https://img.shields.io/badge/status-beta-yellow)

## 🚀 Overview

The **Database Development Assistant (DDA)** is a comprehensive Python-based toolkit designed to streamline MySQL database development, testing, and data management. Built with developers and database administrators in mind, DDA provides intelligent tools for generating realistic test data, validating database schemas, and performing common development tasks efficiently and safely.

## ✨ Features

### **Tool 1: Intelligent Name Randomizer**
- **Smart Database Discovery**: Automatically detects tables with gender and name columns
- **Categorized Names Database**: 100+ names across multiple ethnic/regional groups (English, Arabic, Asian, African)
- **Flexible Configuration**: Update single or multiple name columns based on gender
- **Safe Operations**: Preview changes, backup options, and transaction support
- **Multiple Interfaces**: Both GUI and CLI interfaces available

### **Future Tools Planned**
- Schema Validator & Analyzer
- Bulk Data Generator with relationships
- Data Quality Checker
- Migration Assistant

## 📋 Requirements

- Python 3.8 or higher
- MySQL 8.0 or higher
- 50MB free disk space

## 🛠️ Installation

### Method 1: Direct Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/dda-toolkit.git
cd dda-toolkit

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize the name databases
python scripts/init_names.py
```

### Method 2: Docker (Coming Soon)

```bash
docker pull dda-toolkit/dda:latest
docker run -p 8080:8080 dda-toolkit/dda
```

## 📁 Project Structure

```
dda-toolkit/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── main.py                      # Main entry point
├── config/                      # Configuration files
│   ├── database_config.yaml     # Database connection settings
│   └── tool_config.yaml         # Tool behavior settings
├── data/                        # Data files
│   ├── names/                   # Name databases
│   │   ├── female_names.csv     # Female names (grouped)
│   │   └── male_names.csv       # Male names (grouped)
│   └── sample_datasets/         # Sample data for testing
├── src/                         # Source code
│   ├── core/                    # Core functionality
│   │   ├── database_manager.py  # Database connection & operations
│   │   └── validator.py         # Input validation
│   ├── tools/                   # Individual tools
│   │   ├── name_generator.py    # Name Randomizer Tool
│   │   ├── data_generator.py    # Future: General data generator
│   │   └── schema_validator.py  # Future: Schema analysis
│   ├── ui/                      # User interfaces
│   │   ├── gui_app.py           # Tkinter GUI application
│   │   └── cli_interface.py     # Command-line interface
│   └── utils/                   # Utility functions
│       ├── file_manager.py      # File operations
│       └── logger.py            # Logging configuration
├── scripts/                     # Utility scripts
│   ├── init_names.py            # Initialize name databases
│   └── backup_tool.py           # Database backup utility
├── tests/                       # Test suite
│   ├── test_name_generator.py
│   └── test_database_manager.py
└── docs/                        # Documentation
    ├── user_guide.md
    └── api_reference.md
```

## 🎯 Quick Start

### GUI Mode (Recommended for Beginners)

```bash
# Launch the graphical interface
python main.py --gui
```

### CLI Mode (For Automation & Advanced Users)

```bash
# Show available commands
python main.py --help

# Run Name Randomizer Tool
python main.py --tool name-generator --db your_database --table employees
```

## 🛠️ Using the Name Randomizer Tool

### Step-by-Step Guide

1. **Launch the Tool**
   ```bash
   python main.py --gui
   ```

2. **Configure Database Connection**
   - Enter MySQL host, port, username, and password
   - Click "Test Connection" to verify
   - Select your database from the dropdown

3. **Select Target Table**
   - Choose a table from the detected list (tables with gender columns)
   - View table schema and sample data
   - Select gender column (auto-detected)
   - Select name column(s) to update

4. **Configure Name Settings**
   - Choose gender(s) to update: Male, Female, or Both
   - Select name groups: English, Arabic, Asian, African, or All
   - Set distribution: Equal chance or Proportional (matching group sizes)
   - Configure update scope: All rows or filtered subset

5. **Preview & Execute**
   - Click "Preview Changes" to see sample updates
   - Choose backup options (recommended)
   - Select "Dry Run" to test without changes
   - Click "Execute Update" to apply changes

### Example CLI Commands

```bash
# Update female first names with English and Arabic names
python main.py --tool name-generator \
               --host localhost \
               --user root \
               --db company_db \
               --table employees \
               --gender-col gender \
               --name-col first_name \
               --gender female \
               --groups English,Arabic \
               --distribution proportional

# Update both genders in multiple name columns
python main.py --tool name-generator \
               --db customer_db \
               --table customers \
               --gender-col sex \
               --name-col "first_name,last_name" \
               --gender both \
               --groups all \
               --where "age > 18" \
               --limit 1000 \
               --backup yes

# Preview changes without executing
python main.py --tool name-generator \
               --db test_db \
               --table users \
               --dry-run yes \
               --preview-rows 20
```

## 📊 Name Database

The tool comes pre-loaded with categorized names:

### Female Names (100+ names)
- **60 English/Western**: Emma, Olivia, Ava, Sophia, Charlotte...
- **20 Arabic**: Fatima, Aisha, Zainab, Mariam, Sarah...
- **20 Asian/African**: Mei, Sakura, Priya, Amina, Zahara...

### Male Names (100+ names)
- **60 English/Western**: James, John, Robert, Michael, William...
- **20 Arabic**: Mohammed, Ali, Omar, Ahmed, Hassan...
- **20 Asian/African**: Wei, Kenji, Kwame, Chijioke, Tunde...

### Customizing Name Databases

Edit the CSV files in `data/names/` to add your own names:

**Format:**
```csv
group,name
English,Emma
English,Olivia
Arabic,Fatima
Arabic,Aisha
Asian,Mei
African,Zahara
```

**To add new names:**
```bash
# Edit the CSV files directly
nano data/names/female_names.csv

# Or use the included management script
python scripts/manage_names.py --add --gender female --group "NewGroup" --name "NewName"
```

## ⚙️ Configuration

### Database Configuration (`config/database_config.yaml`)

```yaml
default_connection:
  host: localhost
  port: 3306
  user: root
  charset: utf8mb4
  connection_timeout: 10

backup_settings:
  enabled: true
  location: ./backups
  keep_last: 5

safety_settings:
  max_rows_per_update: 10000
  require_confirmation: true
  transaction_size: 1000
```

### Tool Configuration (`config/tool_config.yaml`)

```yaml
name_generator:
  default_distribution: proportional
  allow_duplicates: false
  preserve_null: true
  case_sensitive: false
  
logging:
  level: INFO
  file: ./logs/dda.log
  max_size_mb: 10
  backup_count: 5
```

## 🔧 Advanced Usage

### Custom SQL Filters

```bash
# Update names with custom WHERE clause
python main.py --tool name-generator \
               --db mydb \
               --table users \
               --where "department = 'Sales' AND hire_date > '2023-01-01'"
```

### Batch Processing for Large Tables

```bash
# Process in batches of 5000 rows
python main.py --tool name-generator \
               --db large_db \
               --table huge_table \
               --batch-size 5000 \
               --threads 4
```

### Integration with Scripts

```python
# Use as a Python module
from src.tools.name_generator import NameRandomizer

randomizer = NameRandomizer(host='localhost', user='root', database='mydb')
config = {
    'table': 'employees',
    'gender_column': 'gender',
    'name_columns': ['first_name'],
    'target_gender': 'female',
    'name_groups': ['English', 'Arabic']
}
result = randomizer.execute_update(config)
```

## 🧪 Testing

Run the test suite to ensure everything works correctly:

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_name_generator.py -v

# Run with coverage report
python -m pytest tests/ --cov=src --cov-report=html
```

## 📝 Logging

The tool provides comprehensive logging:

- **Application Logs**: `logs/dda.log`
- **Change Logs**: `logs/changes/` (per-execution)
- **Error Logs**: `logs/errors/`

View logs in real-time:
```bash
tail -f logs/dda.log
```

## 🔒 Security Considerations

1. **Never commit credentials**: Database credentials are stored in config files excluded from git
2. **Use environment variables** for production:
   ```bash
   export DDA_DB_PASSWORD="your_secure_password"
   ```
3. **Backup before operations**: Always enable backup for production databases
4. **Use read-only mode first**: Preview changes before executing
5. **Limit permissions**: Use database users with minimal required permissions

## 🤝 Contributing

We welcome contributions! Here's how to help:

1. **Report Bugs**: Use the GitHub issue tracker
2. **Suggest Features**: Open an issue with the "enhancement" label
3. **Submit Code**: Fork the repo and create a pull request
4. **Improve Documentation**: Help us make the docs better

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/dda-toolkit.git
cd dda-toolkit

# Install development dependencies
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install

# Create a feature branch
git checkout -b feature/amazing-feature
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with ❤️ for the database development community
- Names databases curated from various open sources
- Inspired by real-world database development challenges

## 📞 Support

- **Documentation**: [docs.dda-toolkit.org](https://docs.dda-toolkit.org)
- **Issues**: [GitHub Issues](https://github.com/yourusername/dda-toolkit/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/dda-toolkit/discussions)
- **Email**: support@dda-toolkit.org

## 🚀 Roadmap

### Version 1.1 (Next Release)
- [ ] Schema Validator Tool
- [ ] Export/Import name databases
- [ ] Docker support

### Version 1.2
- [ ] Bulk Data Generator
- [ ] Web-based GUI
- [ ] PostgreSQL support

### Version 2.0
- [ ] Multi-database operations
- [ ] Machine learning for name suggestions
- [ ] API server mode

---

**Happy Database Developing!** 🎉

*If you find this tool useful, please give it a ⭐ on GitHub!*
