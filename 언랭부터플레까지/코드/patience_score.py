#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import matplotlib as ml
import json
import requests
import time
import pickle

class Patience :    #끈기점수를 연산하기 위한 클래스. 필드 key, summonerName이 필요해 클래스를 선언하였다.
    key = ''    #riot api를 불러오기 위한 api key를 필드로 선언한다.
    summonerName = ''    #한명의 유저에 대한 끈기 점수를 계산해야된므로 매개변수로 줄 summonerName을 필드로 선언한다.
    
    def __init__(self, key, summonerName) :
        self.key = key
        self.summonerName = summonerName

    def get_patience_score(self) :    #최종 결과(I or R)을 반환한다.
        
        accountId = get_accountId(self.key, self.summonerName)   
        #매개변수로 준 summonerName의 account id.이게 있어야 유저의 match list를 불러올 수 있다.
        matchlists_list = get_matchlists(self.key, accountId)
        #account id를 통해 유저의 match list를 불러온다. dictionary-list형태이다.
        matchlists_df = pd.DataFrame(matchlists_list)
        #dictionary-list형태를 dataframe형태로 변환해준다. 
        
        matches_list = []
        for i in list(matchlists_df['gameId']) :
            match = get_matches(self.key, i)
            matches_list.append(match) 
        #match list df의 game id를 이용해 개별 매치에 대한 정보를 불러온다.
        #for문을 통해 모든 매치에 대한 정보를 불러온다.

        mode_win_duration_df = get_mode_win_duration(self.summonerName, matches_list)
        #matches_list에서 game mode, win, game duration에 대한 정보를 불러와 데이터프레임으로 만든다.        
       
        loseGames_df = get_loseGame(mode_win_duration_df)
        #mode_win_duration에서 win = fail인 row만 추출한 데이터프레임.        
     
    
        classicGame_df = get_classic(loseGames_df)
        #loseGames_df에서 gameMode = CLASSIC인 row만 추출한 데이터프레임        
     
        
        patience_score = get_patienceScore(classicGame_df)
        #loseGames_df에서 끈기점수를 계산하여 리턴한다.

        return patience_score
        
def get_mode_win_duration(summonerName, matches_list) : #전체 게임 리스트 input : list, output : dataframe
        dic = {'gameId' : [],'gameMode' : [],'win' : [], 'duration' : []}

        for match in matches_list :
            if not "gameId" in match.keys() and not 'gameDuration' in match.keys() and not 'gameMode' in match.keys() :
                continue


            g_id = match['gameId']
            participantId = 0
            win = ''
            gameMode = match['gameMode']
            duration = 0

            for i in match['participantIdentities'] : #각각의 게임 정보 - win 정보
                if i['player']['summonerName'] == summonerName : 
                    participantId = i['participantId']
                    break

            if participantId > 0 and participantId <= 5 :
                team = 100
            else : 
                team = 200


            if team == 100 :
                win = match['teams'][0]['win']
            else : 
                win = match['teams'][1]['win']

            duration = match['gameDuration']/60 #초 단위의 gameDuration을 분단위로 바꾼다. 

            dic['gameId'].append(g_id)
            dic['gameMode'].append(gameMode)
            dic['win'].append(win)
            dic['duration'].append(duration)

        df = pd.DataFrame(dic)
        return df

def get_matches(key, gameId) : #매치정보 불러오기 input:int, output:dict
    url = "https://kr.api.riotgames.com/lol/match/v4/matches/"+str(gameId)+"?api_key="+key
    match = requests.get(url)

    while match.status_code == 429:
            time.sleep(5)
            url = 'https://kr.api.riotgames.com/lol/match/v4/matches/' + str(gameId) + '?api_key=' + key 
            match = requests.get(url)

    match = match.json()
    
    return match

def get_matchlists(key, accountId) : #매치리스트 불러오기  input : str, output : list 
    url = "https://kr.api.riotgames.com/lol/match/v4/matchlists/by-account/"+accountId+"?api_key="+key
    matchlists = requests.get(url)    
    matchlists = matchlists.json()['matches']
    return matchlists

def get_accountId(key, summonerName) : #accountId 불러오기 input:str, output:str  
    url = "https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/"+summonerName+"?api_key="+key
    summoner = requests.get(url)    
    summoner = summoner.json()
    return summoner["accountId"]

def get_patienceScore(df) : #patience score를 리턴, input:df, output:int
    #short_game : 진 경기중 15분 이상 20분 미만인 게임
    short_game = df[(df['duration']>=15) & (df['duration']<20)]
    #normal_game : 진 경기중 20분 이상인 게임
    normal_game = df[df['duration']>=20]

    short_game_cnt = len(short_game)
    normal_game_cnt = len(normal_game)

    #short_game의 비율을 구해 끈기점수를 계산한다.
    result = 100-short_game_cnt/normal_game_cnt*100

    return round(result,4)

def get_classic(df) : #일반게임 추출. input:df, output:df
    classicGames_df = df[df['gameMode'] == 'CLASSIC']
    return classicGames_df

def get_loseGame(df) :  #진게임만 남기는 메소드, input : df, output : df
    df2 = df.copy()
    indexNums = df2[df2['win'] == 'Win'].index
    df2.drop(indexNums, inplace = True)
    return df2

