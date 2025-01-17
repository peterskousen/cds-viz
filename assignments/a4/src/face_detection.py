import os
import torch
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image

''' This solves an error with some corrupted files in the dataset not accepted by Pillow'''
ImageFile.LOAD_TRUNCATED_IMAGES = True 
from PIL import ImageFile

from tqdm.auto import tqdm
from facenet_pytorch import MTCNN

def define_path():
    inpath = os.path.join("in", "newspapers")
    outpath = os.path.join("out")
    return inpath, outpath


def process_images(inpath, mtcnn):
    '''
    Process images, detect faces using MTCNN
    '''
    print("Processing images...")
    results = []
    for newspaper in os.listdir(inpath):
        print(f'Currently processing folder: {newspaper}...')
        paper_path = sorted(os.listdir(os.path.join(inpath, newspaper)))
        for page in tqdm(paper_path, position=0, leave=True):
            '''
                - Some image data are corrupted and do not work with Pillow. The following exception handler skips affected files.
            '''
            try:
                img = Image.open(os.path.join(inpath, newspaper, page))
            except OSError as e:
                print(f"Error processing image: {e}, skipping")
                continue
            boxes, _ = mtcnn.detect(img)
            results.append([page, boxes])
    return results


def convert_list_values(results):
    '''
        - The MTCNN returns embeddings as a list of bounding box coordinates.
        - If no faces are detected, MTCNN returns None; these values are converted to an int (i.e. 0);
        - Detected faces are returned as a list of floats representing bounding box coordinates; These are converted to an int describing the amount of faces.
    '''
    for obj in results:
        if obj[1] is None:
            obj[1] = 0
        else:
            obj[1] = len(obj[1])
    return results


def process_dataframe(results, outpath):
    '''
        - Processes face detection results into a dataframe
        - Extracts newspaper name and decade from the file name
        - Sorts df by decade and groups all entries by decade and newspaper
        - Calculates % of pages w/ faces
    '''

    df = pd.DataFrame(results, columns=["Pages", "Faces freq."])
    df['Year'] = df['Pages'].str.extract(r'-(\d{4})-').astype(int)
    df['Paper'] = df['Pages'].str.extract(r'^([A-Z]{3})-').astype(str)
    df['Decade'] = (df['Year'] // 10) * 10

    df_sorted = df.sort_values('Decade')

    grouped_df = df_sorted.groupby(['Decade', 'Paper']).agg({
        'Faces freq.':'sum',
        'Pages': 'count',
    }).reset_index()

    grouped_df['% of pages'] = (grouped_df['Faces freq.'] / grouped_df['Pages']) * 100
    grouped_df['% of pages'] = grouped_df['% of pages'].round(2)
    grouped_df.to_csv(os.path.join(outpath,"data.csv"), index=False)
    return grouped_df


def plot_data(grouped_df, outpath):
    '''
    Plot % of faces / page / decade for all three newspapers
    '''
    papers = grouped_df['Paper'].unique()
    plt.figure(figsize=(12, 4))
    for paper in papers:
        paper_df = grouped_df[grouped_df['Paper'] == paper]
        plt.plot(paper_df['Decade'], paper_df['% of pages'], label=paper)
    plt.xticks(grouped_df['Decade'].unique(), grouped_df['Decade'].unique())
    plt.xlabel('Decade')
    plt.ylabel('% of pages')
    plt.title('Newspaper pages containing faces')
    plt.legend()
    plt.savefig(os.path.join(outpath, "plot.png"))
    plt.show()


def main():
    
    mtcnn = MTCNN(keep_all=True)

    inpath, outpath = define_path()

    results = process_images(inpath, mtcnn)

    results = convert_list_values(results)

    grouped_df = process_dataframe(results, outpath)

    plot_data(grouped_df, outpath)


if __name__ == "__main__":
    main()
