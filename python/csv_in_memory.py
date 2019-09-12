import csv
import StringIO

f = StringIO.StringIO()
leads_file = csv.writer(f, delimiter='\t')
leads_file.writerow(
        ["Organization Name", "Location Name", "Zipcode", "# of Participants"]
    )
# ...

print f.getvalue()
