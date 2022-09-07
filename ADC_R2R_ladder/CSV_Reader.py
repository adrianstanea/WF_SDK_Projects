import csv


def import_csv_data(path):
    rows = []
    with open(path) as file:
        reader = csv.reader(file)

        for row in reader:
            # print(row)
            rows.append(int(row[0]))

    return rows


# test if data is imported correctly

# data = import_csv_data("Waveforms/sine.csv")
# print(data)
# print(len(data))
