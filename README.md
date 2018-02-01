README.md

example of ~/.ssh/identity.yaml file:


current-project: project_1_name

freshbooks:
    api:
        url: https://company-name.freshbooks.com/api/2.1/xml-in
        secret: 786qe76er86e767fgdfs8g6876
        user-agent: commandline-utils/1.0
    login-url: https://company-name.freshbooks.com/
    
project_1_name:        
    freshbooks: 
        client-id: 9999999999
        task-id: 99999
        project-id: 999
    expected-weekly-total: 37.5
    daily-hours: 7.5
    timesheets:
        url: https://us1.dovico.net/dovico0520/navviewmanager.aspx
        url: https://additional-timesheet.web.com/login
    invoice-frequency: weekly
        
