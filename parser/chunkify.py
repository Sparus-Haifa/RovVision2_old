# split csv records to chunks of 300 rows and save them all in a new csv file

import pandas as pd
import numpy as np
import os


def split_csv(csv_path, chunk_size=300):
    df = pd.read_csv(csv_path)
    # print(df.head())

    # load the sections.csv file
    sections_df = pd.read_csv(os.path.join(os.path.dirname(csv_path), 'sections.csv'), index_col=0)

    chunks_df = pd.DataFrame(columns=['section', 'chunk', 'first_image', 'last_image'])

    total_number_of_chunks = 0

    # iterate over the sections
    for index, row in sections_df.iterrows():
        # get the first and last image
        first_image = row['first_image']
        last_image = row['last_image']
        print('first_image', first_image)
        print('last_image', last_image)

        # get the df for this section
        section_df = df[(df['Index'] >= first_image) & (df['Index'] <= last_image)]
        # print('section_df', section_df.shape)
        # print(section_df.head())

        # split the df to chunks of maximum chunk_size rows and minumum 1 row
        chunks = np.array_split(section_df, max(1, section_df.shape[0] // chunk_size + 1))
        # print('chunks', len(chunks))
        # print(chunks[0].head())

        # add the chunks to the chunks_df
        for i, chunk in enumerate(chunks):
            # print('chunk', chunk.shape)
            # print(chunk.head())
            chunks_df = chunks_df.append({'section': row['bagfile'], 'chunk': i, 'first_image': chunk['Index'].iloc[0], 'last_image': chunk['Index'].iloc[-1]}, ignore_index=True)

        total_number_of_chunks += len(chunks)
        
    # save the chunks to a new csv file
    chunks_df.to_csv(os.path.join(os.path.dirname(csv_path), 'chunks.csv'), header=True)
    print('total_number_of_chunks', total_number_of_chunks)



    print('done')

if __name__ == '__main__':
    csv_path = r'bags/pairs.csv'
    split_csv(csv_path)

    

