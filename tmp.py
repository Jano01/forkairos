from forkairos import get_provider 
for name in ['gfs', 'ecmwf_open']: 
    p = get_provider(name) 
    print(f'\n--- {name} ---') 
    for k in p.available_variables(): 
        print(f'  {k}') 
