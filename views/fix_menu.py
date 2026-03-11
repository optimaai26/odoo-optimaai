import re

with open('c:/Users/Hp/Desktop/odoo/optimaai/views/menu_views.xml', 'r', encoding='utf-8') as f:
    content = f.read()

# The Menus block is between <!-- Main Menu --> and <!-- Access Request Views and Action -->
menus_start = content.find('    <!-- Main Menu -->')
views_start = content.find('    <!-- ==========================================\n         Access Request Views and Action')

if menus_start != -1 and views_start != -1:
    header = content[:menus_start]
    menus = content[menus_start:views_start]
    views = content[views_start:content.find('</odoo>')]
    
    new_content = header + views + menus + '</odoo>\n'
    
    with open('c:/Users/Hp/Desktop/odoo/optimaai/views/menu_views.xml', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Fixed menu_views.xml")
else:
    print("Could not find blocks")
