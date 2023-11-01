from supervisedGIAnt import SupervisedGIAnt

main_dir = '../content/drive/MyDrive/s2/'
sg = SupervisedGIAnt(budget=1000, qPairs = 100, delimiter='\t',  sourceFilePath=main_dir + 'sourceSample.tsv', targetFilePath=main_dir + 'targetSample.tsv')
sg.applyProcessing()
