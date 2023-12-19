import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import percentileofscore
from cachetools import cached
import matplotlib.pyplot as plt
import pymysql
pymysql.install_as_MySQLdb()

PAGE_CONFIG = {"page_title":"More Examples","page_icon":"💯","layout":"centered"}
st.set_page_config(**PAGE_CONFIG)

from sqlalchemy import create_engine
conn_string = 'mysql://{user}:{password}@{host}:{port}/{db}?charset={encoding}'.format(
    user='daily_screamer', 
    password='sF5pxbMLBg8=', 
    host = 'jsedocc7.scrc.nyu.edu', 
    port     = 3306, 
    encoding = 'utf8',
    
    db = 'daily_screamer'
)
engine = create_engine(conn_string)

cas = pd.read_sql("SELECT * FROM CASCE1", engine)
stern = pd.read_sql("SELECT * FROM SternCE1", engine)

casQuality = cas['qualityPCA'].values
casDifficulty = cas['difficultyPCA'].values

casProfQuality = cas.groupby('instructor')['qualityPCA'].mean().values
casProfDifficulty = cas.groupby('instructor')['difficultyPCA'].mean().values

sternQuality = stern['qualityPCA'].values

cas.insert(7, 'qualityRating', pd.qcut(cas.qualityPCA, 5, labels = ['horrendous', 'bad','decent','good','excellent']))
cas.insert(7, 'difficultyRating', pd.qcut(cas.difficultyPCA, 5, labels = ['very easy', 'easy','average','challenging','very challenging']))

stern.insert(6, 'qualityRating', pd.qcut(stern.qualityPCA, 5, labels = ['horrendous', 'bad','decent','good','excellent']))

def hist_all_courses(sql, engine):
    df_courses = pd.read_sql_query(sql, con=engine)
    fig = df_courses.OverallEvaluationCourse.hist().get_figure()
    st.pyplot(fig) 


def show_course_based_on_difficulty(difficulty, df, department = None, show_CE_result = True):

    d = df['difficultyPCA'].values
    diffPercentiles = np.percentile(d, [0, 20, 40, 60, 80, 100])
    indices = np.argwhere((d >= diffPercentiles[difficulty]) & (d <= diffPercentiles[difficulty+1])).flatten()
    

    if show_CE_result:
        result = df.iloc[indices]
    else:
        try:
          result = df.loc[indices][['courseCode',	'courseSection',	'courseName',	'instructor', 'qualityRating', 'difficultyRating']]
        except:
          result = df.loc[indices][['courseCode',	'courseSection',	'courseName',	'instructor', 'qualityRating']]

    result['quality'] = df['qualityPCA'].values[indices]


    if department:
        return result[result.courseCode.str.contains(str.upper(department))].sort_values('quality', ascending = False).drop('quality', axis = 1)
        
    return df.iloc[indices].drop('quality', axis = 1)



def show_course_based_on_quality(quality, df, department = None, show_CE_result = True, isCAS = True):

    d = df['qualityPCA'].values
    qualPercentiles = np.percentile(d, [0, 20, 40, 60, 80, 100])
    indices = np.argwhere((d >= qualPercentiles[quality]) & (d <= qualPercentiles[quality+1])).flatten()
    

    if show_CE_result:
        result = df.iloc[indices] 
    else:
        if isCAS:
            result = df.loc[indices][['courseCode',	'courseSection',	'courseName',	'instructor', 'qualityRating','difficultyRating']]
        else:
            result = df.loc[indices][['courseCode',	'courseSection',	'courseName',	'instructor','intellectuallyStimulating', 'qualityRating']]
   
    if department:
        if isCAS:
            result['difficulty'] = df['difficultyPCA'].values[indices]
            return result[result.courseCode.str.contains(str.upper(department))].sort_values('difficulty', ascending = False).drop('difficulty', axis = 1)
        else:
            return result[result.courseCode.str.contains(str.upper(department))]
      
    if isCAS:
        return df.iloc[indices].drop('quality', axis = 1)

    return df.iloc[indices]


def select_quality_and_difficulty(quality, difficulty, department = None, showCE = False):
  df = cas
  q = cas.qualityPCA.values
  d = cas.difficultyPCA.values

  diffPercentiles = np.percentile(d, [0, 20, 40, 60, 80, 100])
  qualPercentiles = np.percentile(q, [0, 20, 40, 60, 80, 100])

  indices = np.argwhere((d >= diffPercentiles[difficulty]) & (d <= diffPercentiles[difficulty+1]) & (q>=qualPercentiles[quality]) & (q<=qualPercentiles[quality+1])).flatten()

  if showCE:
    result = df.iloc[indices]
  else:
    result = df.loc[indices][['courseCode',	'courseSection',	'courseName',	'instructor', 'qualityRating','difficultyRating']]

  if department:
    return result[result.courseCode.str.contains(str.upper(department))]

  return result

def plotCourseOn2D(course, courseCode):
  fig, ax = plt.subplots(figsize = (10, 6))
  ax.scatter(cas.qualityPCA, cas.difficultyPCA, label = "All Courses", s = 2, color = "grey")
  ax.scatter(course.qualityPCA, course.difficultyPCA, label = "All %s" % courseCode, color = "lawngreen")
  ax.scatter(course.qualityPCA.mean(), course.difficultyPCA.mean(), label = "Average of %s" % courseCode, color = "cyan")
  ax.plot([cas.qualityPCA.mean()] * 2, [cas.difficultyPCA.min(), cas.difficultyPCA.max()], c = 'orange', label = 'Mean Quality')
  ax.plot([cas.qualityPCA.min(), cas.qualityPCA.max()], [cas.difficultyPCA.mean()]*2, c = 'orange', label = 'Mean Difficulty')
  ax.set_xlabel("Overall Quality")
  ax.set_ylabel("Difficulty")
  ax.legend()
  return fig

    

def main():
    st.title("Welcome!")
    st.subheader("Find your perfect match")
    menu = ["Home","CAS & Stern Course Summary", "CAS Course Search", "Stern Course Search"]
    choice = st.sidebar.selectbox('Menu',menu)
    if choice == 'Home':
      st.image(
            "https://media.designrush.com/inspirations/129660/conversions/_1521486208_365_NYUPreviewImage-preview.jpg",
            width=400, # Manually Adjust the width of the image as per requirement
        )


    if choice == 'CAS & Stern Course Summary':
        st.subheader("Below is a summary of the overall ratings for Stern courses")
        SQL_script = st.text_area(label='SQL Input', value='select OverallEvaluationCourse from SternCE1 LIMIT 10000')
        hist_all_courses(SQL_script, engine)
        st.subheader("Below is a summary of the overall ratings for CAS courses")
        SQL_script = st.text_area(label='SQL Input', value='select OverallEvaluationCourse from CASCE1 LIMIT 10000')
        hist_all_courses(SQL_script, engine)

    elif choice == 'CAS Course Search':
        st.subheader("Search Courses by Department Code", anchor=None)

        show_by_difficulty = st.checkbox('By Difficulty')
        difficulty = st.slider('**Select the difficulty level**', 1,5)
        show_by_quality = st.checkbox('By Quality')
        quality = st.slider('**Select the quality level**', 1,5)
        show_CE_result = st.checkbox('display course evaluation ratings')
        department_code_difficulty = st.text_input('**By CAS Department Code**')

        if department_code_difficulty:
          if show_by_difficulty and show_by_quality:
            result= select_quality_and_difficulty(difficulty-1,quality-1, department = department_code_difficulty, showCE = show_CE_result)
            st.dataframe(result)
          if not show_by_difficulty and show_by_quality:
            result = show_course_based_on_quality(quality-1, cas, department = department_code_difficulty, show_CE_result = show_CE_result, isCAS = True)
            st.dataframe(result)
          if show_by_difficulty and not show_by_quality:
            result = show_course_based_on_difficulty(difficulty-1, cas, department = department_code_difficulty, show_CE_result = show_CE_result)
            st.dataframe(result)

        st.markdown("""---""")

        st.subheader("Search Courses by Course Code", anchor=None)
        course_code = st.text_input('By CAS Course Code')
        if course_code:
          courses = cas[cas.courseCode == course_code].iloc[:, 2:] #pd.read_sql("select * from CASCE1 where courseCode = '" + course_code +"'", con=engine)
          Dpercentile = None
          Qpercentile = None
          if len(courses) != 0:
            st.dataframe(courses.sort_values('qualityPCA', ascending = False).drop(['qualityPCA', 'difficultyPCA'], axis = 1))
            Dpercentile = percentileofscore(casDifficulty, courses['difficultyPCA'].mean())
            Qpercentile = percentileofscore(casQuality, courses['qualityPCA'].mean())
          if Dpercentile:
            st.write("Difficulty percentile in CAS courses: %.3f" % Dpercentile)

          if Qpercentile:
            st.write("Quality percentile in CAS courses: %.3f" % Qpercentile)
            st.pyplot(plotCourseOn2D(courses, course_code))
          
          else: st.write("Course not found")

        st.markdown("""---""")

        st.subheader("Search Courses by Professor Name", anchor=None)
        professor_name = st.text_input('By CAS Professor Name')
        
        if professor_name:
          profs = cas[cas.instructor == professor_name].iloc[:, 2:]  #pd.read_sql("select * from CASCE1 where instructor = '" + professor_name +"'", con=engine)
          Dpercentile = None
          Qpercentile = None

          if len(profs) != 0:
            st.dataframe(profs.sort_values('qualityPCA', ascending = False).drop(['qualityPCA', 'difficultyPCA'], axis = 1))
            Dpercentile = percentileofscore(casProfDifficulty, profs['difficultyPCA'].mean())
            Qpercentile = percentileofscore(casProfQuality, profs['qualityPCA'].mean())
          if Dpercentile:
            st.write("Difficulty percentile in CAS professors: %.3f" % Dpercentile)

          if Qpercentile:
            st.write("Quality percentile in CAS professors: %.3f" % Qpercentile)
            st.pyplot(plotCourseOn2D(profs, professor_name))
          
          else: st.write("Course not found")


    elif choice == 'Stern Course Search':
        st.subheader("Search Department Courses by Quality", anchor=None)
        quality = st.slider('Select the quality level', 1,5)
        show_CE_result = st.checkbox('display course evaluation ratings')
        department_code_stern = st.text_input('By Stern Department Code')
        if department_code_stern:
            result = show_course_based_on_quality(quality-1, stern, department = department_code_stern, show_CE_result = show_CE_result, isCAS = False)
            st.dataframe(result)

        st.markdown("""---""")
       
        st.subheader("Search Courses by Course Code", anchor=None)
        course_code_stern = st.text_input('By Stern Course Code')
        if course_code_stern:
            st.dataframe(stern[stern.courseCode == course_code_stern])

        st.markdown("""---""")

        st.subheader("Search Courses by Professor Name", anchor=None)
        professor_name_stern = st.text_input('By Stern Professor Name')
        if professor_name_stern:
            st.dataframe(stern[stern.instructor == professor_name_stern].drop('qualityPCA', axis = 1)) 
                  
          
if __name__ == '__main__':

    main()