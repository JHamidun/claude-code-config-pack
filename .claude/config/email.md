# Email Accounts

> Add your email accounts here.

| Account | Server | Protocol |
|---------|--------|----------|
| your-email@gmail.com | smtp.gmail.com | IMAP/SMTP |
| your-work-email@company.com | mail.company.com | Exchange/EWS |

## Gmail (App Password)
```python
import smtplib, os
password = os.getenv('GMAIL_APP_PASSWORD')
```

## Exchange
```python
from exchangelib import Account, Credentials, Configuration
password = os.getenv('EXCHANGE_PASSWORD')
config = Configuration(server='mail.company.com',
                       credentials=Credentials(email, password))
```
