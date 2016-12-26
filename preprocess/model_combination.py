# coding=utf-8
# import knn_wpm_dpm
# import impaired_classification
import global_variables
from os import listdir
from sklearn.metrics import classification_report
from sklearn.metrics import accuracy_score
from sklearn.utils import shuffle

from impaired_classification import ImpairedClassification
from tension_measuring.knn_dpm import KnnDpmWpm


def main():
    # Hold f1 scores for each model
    f1_scores = []
    impaired_model = ImpairedClassification('TrainSubtitles', 'TestSubtitles')
    knn_model = KnnDpmWpm('TrainSubtitles', 'TestSubtitles')

    # impaired_model.tune_and_train()
    models = [impaired_model, knn_model]

    test_folder = 'CategoryDataTest'
    categories = global_variables.genres
    files = []
    y_true = []
    y_pred = []

    for category in categories:
        input_folder_path = "%s/%s" % (test_folder, category)
        print('.', )

        file_paths = []
        for f in listdir(input_folder_path):
            path = "%s/%s" % (input_folder_path, f)
            file_paths.append(path)

        for path in file_paths:
            y_true.append(category)
            files.append(path)

    for model in models:
        f1_scores.append(model.get_f1_scores())
    #print(f1_scores)

    for idx, filepath in enumerate(files):
        predicteds = []
        for model in models:
            predicted = model.predict(filepath)
            if predicted == None:
                print("none: ", filepath)
            predicteds.append(predicted)
            #print('model: ', model, 'predicted:', predicted, 'true:', y_true[idx])

        max_f1 = 0
        best_predict = 0
        for i, predicted in enumerate(predicteds):
            #print(f1_scores[i][predicted])
            try:
                if max_f1 < f1_scores[i][predicted]:
                    max_f1 = f1_scores[i][predicted]
                    best_predict = predicted
            except:
                print("error ", i, predicted)
        y_pred.append(best_predict)
        #print("best predict", best_predict)
        #break
    print('accuracy: ', accuracy_score(y_true, y_pred))
    print(classification_report(y_true, y_pred))

main()


