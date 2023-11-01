from extrapolation import Extrapolation

main_dir = '../content/drive/MyDrive/s2/'
x=0
print('Enter desired recall:')
x = input()
sg = Extrapolation(budget=1000, qPairs = 100, delimiter='\t',  sourceFilePath=main_dir + 'sourceSample.tsv', targetFilePath=main_dir + 'targetSample.tsv', users_input=float(x))
sg.applyProcessing()
