# Create your views here.
# Authors: Liu Haobing, Li Juan, Zhu Jing, Li Zexuan
# Organization: Shanghai Jiao Tong University
from __future__ import division
from __future__ import unicode_literals

from django.http import JsonResponse
from django.shortcuts import render_to_response
from django.shortcuts import HttpResponse
from django.shortcuts import render
from web import models
from django.contrib.auth.decorators import login_required
from web.models import *
import json
import time
import xlrd
import xlwt
import numpy as np
import datetime
# from datetime import *
from django.db.models import Count, Avg, Max, Min, Sum
import numpy as np
import pandas as pd
# import csv
# import matplotlib.pyplot as plt
import keras
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import Masking
# from sklearn.model_selection import train_test_split
# from sklearn.preprocessing import MinMaxScaler
# from sklearn.metrics import mean_squared_error
# from keras.layers import Bidirectional
# #from keras.preprocessing.sequence import pad_sequences

from django.db import connection
from .recommend_util import *


# Create your views here.
@login_required
def home(request):
    return render(request, 'servermaterial/home.html')


def admin(request):
    return render(request, 'servermaterial/admin_index.html')


def login(request):
    if request.method == 'POST':
        if 'turn2register' in request.POST:
            return render(request, 'servermaterial/register.html')
        username = request.POST['id_username']
        passwd = request.POST['id_password']
        message = '所有字段都必须填写！'
        if username and passwd:
            if Register.objects.filter(UserName=username):
                record = Register.objects.filter(UserName=username).values()[0]
                db_password = record['Password']
                if passwd == db_password:
                    request.session['state'] = True
                    request.session['userName'] = record['Name']
                    return JsonResponse({'info': 'success', 'userName': record['Name']})
                else:
                    message = '密码错误！'
            else:
                message = '用户名不存在！'
        # return render(request, 'servermaterial/login.html', {'error_info': message})
        return JsonResponse({'info': message})
    else:
        request.session.clear()
    return render(request, 'servermaterial/login.html')


def reset(request):
    if request.method == 'POST':
        username = request.POST["data[0][username]"]
        email = request.POST["data[1][email]"]
        rstpasswd = request.POST["data[2][rstpasswd]"]
        rstrepasswd = request.POST["data[3][rstrepasswd]"]
        message = '所有字段都必须填写！'
        if not (username and email and rstpasswd and rstrepasswd):
            return HttpResponse(json.dumps({'message': message}))
        if not models.Register.objects.filter(UserName=username, Email=email):
            message = '该用户不存在！'
            return HttpResponse(json.dumps({'message': message}))
        if rstrepasswd != rstpasswd:
            message = '两次输入的密码不相同！'
            return HttpResponse(json.dumps({'message': message}))
        if len(rstpasswd) < 6:
            message = '密码长度太短！请设置6-20位密码！'
            return HttpResponse(json.dumps({'message': message}))
        if len(rstpasswd) > 20:
            message = '密码长度太长！请设置6-20位密码！'
            return HttpResponse(json.dumps({'message': message}))
        temp = models.Register.objects.get(UserName=username, Email=email)
        temp.Password = rstpasswd
        temp.save()
        success = '修改成功！'
        return HttpResponse(json.dumps({'success': success}))


def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        name = request.POST['name']
        password = request.POST['rpassword']
        password_confirm = request.POST['repassword']
        job = request.POST['job']
        school = request.POST['school']
        email = request.POST['email']
        t = time.localtime()
        message = '所有字段都必须填写！'
        date = time.strftime("%b %d %Y %H:%M:%S", t)
        if not (username and name and password and password_confirm and job and school and email):
            return JsonResponse({'message': message})
        if Register.objects.filter(UserName=username):
            message = '该用户已存在'
            return JsonResponse({'message': message})
        if Register.objects.filter(Email=email):
            message = '该邮箱已存在'
            return JsonResponse({'message': message})
        if len(password) < 6:
            message = '密码长度太短，请输入6-20位密码'
            return JsonResponse({'message': message})
        if password != password_confirm:
            message = '两次输入的密码不同，请再次确认'
            return JsonResponse({'message': message})
        else:
            # if department == '校级部门':
            #     authority = 'VIP用户'
            # elif department == '院级部门':
            #     authority = '高级用户'
            # else:
            #     authority = '普通用户'
            Register.objects.create(UserName=username, Name=name, Password=password, Job=job,
                                    Department="校级部门", School=school, Major="all", Grade="b1", Reg=0,
                                    Login=date, Authority="tt", Email=email)
            return JsonResponse({'message': 'success'})

    return render(request, 'servermaterial/login.html', {'message': '新用户创建成功'})


def inquiry(request):
    school = request.POST.get('school')
    time = '20151'
    start_date = datetime.date(2016, 9, 1)
    end_date = datetime.date(2017, 2, 1)
    score_all = list(Score.objects.filter(Semester=time, School=school).values_list('AveScore', flat=True))

    # geo_distribution
    r = list(Basic.objects.filter(School=school).values_list('Province', flat=True))
    province = ['四川', '江西', '江苏', '山东', '安徽', '上海', '重庆', '福建', '河南', '河北', '广东', '广西', '山西', '天津', '湖北', '浙江', '陕西',
                '内蒙古', '海南',
                '辽宁', '吉林', '黑龙江', '湖南', '贵州', '云南', '甘肃', '青海', '台湾', '北京', '西藏', '宁夏', '新疆', '香港', '澳门']
    province_num = {}
    for pro in province:
        province_num[pro] = sum(pro in s for s in r)

    r = list(Score.objects.filter(Semester=time, School=school).values_list('basic__Province', 'AveScore'))
    score_province = {}
    for pro in province:
        a = [float(s[1]) for s in r if pro in s[0]]
        if len(a) == 0:
            score_province[pro] = 0
        else:
            score_province[pro] = sum(a) / len(a)

    # grades
    if len(score_all)==0:
        cdfall=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    else:
        x = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        cdfall = []
        for i in x:
            cdfall.append(sum(float(j) < i for j in score_all) / len(score_all))

    if len(score_all)==0:
        cdfall=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    else:
        x = [-10, 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110]
        pdfall = []
        i = 1
        while i <= 11:
            pdfall.append(sum((x[i - 1] + x[i]) / 2 < float(j) < (x[i] + x[i + 1]) / 2 for j in score_all) / len(score_all))
            i = i + 1

    x = [0, 50, 60, 70, 80, 90, 100]
    num = []
    i = 1
    while i <= 6:
        if i == 6:
            num.append(sum(x[i - 1] <= float(j) <= x[i] for j in score_all))
        else:
            num.append(sum(x[i - 1] <= float(j) < x[i] for j in score_all))
        i = i + 1

    # the average grade for different gender
    score_male = list(
        Score.objects.filter(Semester=time, School=school, basic__Gender='1').values_list('AveScore', flat=True))
    if len(score_male) == 0:
        ave_score_male = 0
    else:
        ave_score_male = sum(float(j) for j in score_male) / len(score_male)

    score_female = list(
        Score.objects.filter(Semester=time, School=school, basic__Gender='0').values_list('AveScore', flat=True))
    if len(score_female)==0:
        ave_score_female = 0
    else:
        ave_score_female = sum(float(j) for j in score_female) / len(score_female)

    if len(score_all) ==0:
        ave_score = 0
    else:
        ave_score = sum(float(j) for j in score_all) / len(score_all)


    # score vs. library
    r = Basic.objects.filter(School=school, score__Semester=time, lib__DateTime__gte=start_date,
                             lib__DateTime__lte=end_date).annotate(count=Count("lib__id")).values('count',
                                                                                                  'score__AveScore')
    score_lib_ave = []
    score_lib_max = []
    score_lib_min = []
    x = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]
    i = 1
    while i <= 9:
        if i == 9:
            re = r.filter(count__gte=x[i - 1], count__lte=x[i])
            if re.count() == 0:
                score_lib_ave.append(0)
                score_lib_max.append(0)
                score_lib_min.append(0)
            else:
                score_lib_ave.append(r.filter(count__gte=x[i - 1], count__lte=x[i]).aggregate(Avg("score__AveScore"))[
                                         'score__AveScore__avg'])
                score_lib_max.append(r.filter(count__gte=x[i - 1], count__lte=x[i]).aggregate(Max("score__AveScore"))[
                                         'score__AveScore__max'])
                score_lib_min.append(r.filter(count__gte=x[i - 1], count__lte=x[i]).aggregate(Min("score__AveScore"))[
                                         'score__AveScore__min'])
        else:
            re = r.filter(count__gte=x[i - 1], count__lt=x[i])
            if re.count() == 0:
                score_lib_ave.append(0)
                score_lib_max.append(0)
                score_lib_min.append(0)
            else:
                score_lib_ave.append(r.filter(count__gte=x[i - 1], count__lte=x[i]).aggregate(Avg("score__AveScore"))[
                                         'score__AveScore__avg'])
                score_lib_max.append(r.filter(count__gte=x[i - 1], count__lte=x[i]).aggregate(Max("score__AveScore"))[
                                         'score__AveScore__max'])
                score_lib_min.append(r.filter(count__gte=x[i - 1], count__lte=x[i]).aggregate(Min("score__AveScore"))[
                                         'score__AveScore__min'])
        i = i + 1

    # score vs. dorm
    start_date = datetime.date(2015, 10, 1)
    end_date = datetime.date(2017, 2, 1)
    # 其实应该算一下每个人的平均回寝时间，存在一张表中，再算;这里为了方便，用了一个近似的算法
    r = list(Basic.objects.filter(School=school, score__Semester=time, dorm__DateTime__gte=start_date,
                                  dorm__DateTime__lte=end_date).values_list('dorm__DateTime', 'score__AveScore'))
    x = [0, 6, 12, 15, 18, 21, 22, 23]
    i = 1
    score_dormtime_ave = []
    score_dormtime_max = []
    score_dormtime_min = []
    while i <= 7:
        if i == 7:
            re = [float(tmp[1]) for tmp in r if x[i] >= tmp[0].hour >= x[i - 1]]
            if len(re) > 0:
                score_dormtime_ave.append(sum(re) / len(re))
                score_dormtime_max.append(max(re))
                score_dormtime_min.append(min(re))
            else:
                score_dormtime_ave.append(0)
                score_dormtime_max.append(0)
                score_dormtime_min.append(0)
        else:
            re = [float(tmp[1]) for tmp in r if x[i] > tmp[0].hour >= x[i - 1]]
            if len(re) > 0:
                score_dormtime_ave.append(sum(re) / len(re))
                score_dormtime_max.append(max(re))
                score_dormtime_min.append(min(re))
            else:
                score_dormtime_ave.append(0)
                score_dormtime_max.append(0)
                score_dormtime_min.append(0)
        i = i + 1

    # health
    # physical test
    # distribution
    health_score_all = list(Health.objects.filter(Semester=2016, School=school).values_list('TotalScore', flat=True))
    x = [0, 50, 60, 70, 80, 90, 100]
    health_num = getdistribution(x, health_score_all)

    # 体质测试与性别
    health_score_male = list(
        Health.objects.filter(Semester=2016, School=school, basic__Gender='1').values_list('TotalScore', flat=True))
    if len(health_score_male) ==0:
        ave_health_score_male = 0
    else:
        ave_health_score_male = sum(float(j) for j in health_score_male) / len(health_score_male)

    health_score_female = list(
        Health.objects.filter(Semester=2016, School=school, basic__Gender='0').values_list('TotalScore', flat=True))
    if len(health_score_female) ==0:
        ave_health_score_female = 0
    else:
        ave_health_score_female = sum(float(j) for j in health_score_female) / len(health_score_female)

    if len(health_score_all) == 0:
        ave_health_score = 0
    else:
        ave_health_score = sum(float(j) for j in health_score_all) / len(health_score_all)




    # 体质与回寝时间
    start_date = datetime.date(2015, 10, 1)
    end_date = datetime.date(2017, 2, 1)
    # 其实应该算一下每个人的平均回寝时间，存在一张表中，再算;这里为了方便，用了一个近似的算法
    # 这里回寝时间多次用到，可以抽取出来
    # 也可以给每个表格加上school和gender属性，就不用join了
    # dorm表格和health表格也可以建立多对多的外键
    r = list(Basic.objects.filter(School=school, health__Semester=2016, dorm__DateTime__gte=start_date,
                                  dorm__DateTime__lte=end_date).values_list('dorm__DateTime', 'health__TotalScore'))
    x = [0, 6, 12, 15, 18, 21, 22, 23]
    i = 1
    health_dormtime_ave = []
    health_dormtime_max = []
    health_dormtime_min = []
    while i <= 7:
        if i == 7:
            re = [float(tmp[1]) for tmp in r if x[i] >= tmp[0].hour >= x[i - 1]]
            if len(re) > 0:
                health_dormtime_ave.append(sum(re) / len(re))
                health_dormtime_max.append(max(re))
                health_dormtime_min.append(min(re))
            else:
                health_dormtime_ave.append(0)
                health_dormtime_max.append(0)
                health_dormtime_min.append(0)
        else:
            re = [float(tmp[1]) for tmp in r if x[i] > tmp[0].hour >= x[i - 1]]
            if len(re) > 0:
                health_dormtime_ave.append(sum(re) / len(re))
                health_dormtime_max.append(max(re))
                health_dormtime_min.append(min(re))
            else:
                health_dormtime_ave.append(0)
                health_dormtime_max.append(0)
                health_dormtime_min.append(0)
        i = i + 1

    # hospital
    # 去校医院次数分布
    # 去校医院次数与性别
    # 去校医院次数与体质
    start_date=datetime.date(2016,7,1)
    end_date=datetime.date(2017,2,1)
    stulist=list(Basic.objects.filter(School=school).values_list('StuID','Gender'))

    if len(stulist) ==0:
        hos_dis=[1,1,1,1,1]
        ave_hos_male=0
        ave_hos_female=0
    else:
        x=[0, 10, 20, 30, 40, 50]
        ave_hos = [HosReg.objects.filter(StuID = stu[0], DateTime__gte=start_date, DateTime__lte=end_date).aggregate(c=Count("id"))['c'] for stu in stulist] #每个人一学期去校医院总次数
        i=1
        hos_dis=[]
        while i <= 5:
            if i==5:
                hos_dis.append(sum(x[i]>=c>=x[i-1] for c in ave_hos))
            else:
                hos_dis.append(sum(x[i]>c>=x[i-1] for c in ave_hos))
            i=i+1
        #性别
        a=[ave_hos[i] for i in range(len(ave_hos)) if stulist[i][1] == '1']
        if len(a)==0:
            ave_hos_male=0
        else:
            ave_hos_male=sum(a)/len(a)

        b=[ave_hos[i] for i in range(len(ave_hos)) if stulist[i][1] == '0']
        if len(b)==0:
            ave_hos_female=0
        else:
            ave_hos_female=sum(b)/len(b)
        ave_hos = sum(ave_hos)/(len(a)+len(b))




    #去校医院次数与体质
    stulist=list(Basic.objects.filter(School=school, health__Semester = 2016).values_list('StuID','health__TotalScore'))
    if len(stulist) ==0:
        hos_health=[0,0,0,0,0,0,0,0,0,0]
        hos_health_max=[0,0,0,0,0,0,0,0,0,0]
        hos_health_min=[0,0,0,0,0,0,0,0,0,0]
    else:
        x=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        hos = [HosReg.objects.filter(StuID = stu[0], DateTime__gte=start_date, DateTime__lte=end_date).aggregate(c=Count("id"))['c'] for stu in stulist] #每个人一学期去校医院总次数
        i=1
        hos_health=[]
        hos_health_min=[]
        hos_health_max=[]
        while i <= 10:
            if i==10:
                a=[float(hos[j]) for j in range(len(hos)) if x[i]>=float(stulist[j][1])>=x[i-1]]
                if len(a)==0:
                    hos_health.append(0)
                    hos_health_min.append(0)
                    hos_health_max.append(0)
                else:
                    hos_health.append(sum(a)/len(a))
                    hos_health_min.append(max(a))
                    hos_health_max.append(min(a))
            else:
                a=[float(hos[j]) for j in range(len(hos)) if x[i]>float(stulist[j][1])>=x[i-1]]
                if len(a)==0:
                    hos_health.append(0)
                    hos_health_min.append(0)
                    hos_health_max.append(0)
                else:
                    hos_health.append(sum(a)/len(a))
                    hos_health_min.append(max(a))
                    hos_health_max.append(min(a))
            i=i+1


    # 校园生活
    # 回寝时间分布
    start_date = datetime.date(2015, 10, 1)
    end_date = datetime.date(2017, 2, 1)
    dorm_all = list(
        Dorm.objects.filter(basic__School=school, DateTime__gte=start_date, DateTime__lte=end_date).values_list(
            'DateTime', flat=True))

    x = [0, 6, 12, 18, 22, 24]
    dorm_num = []
    i = 1
    while i <= 5:
        if i == 5:
            dorm_num.append(sum(x[i] >= r.hour >= x[i - 1] for r in dorm_all))
        else:
            dorm_num.append(sum(x[i] > r.hour >= x[i - 1] for r in dorm_all))
        i = i + 1

    # 回寝时间与性别
    dorm_male = list(Dorm.objects.filter(DateTime__gte=start_date, DateTime__lte=end_date, basic__School=school,
                                         basic__Gender='1').values_list('DateTime', flat=True))
    if len(dorm_male) == 0:
        ave_time_male = 0
        a=0
    else:
        time_male = [r.hour * 3600 + r.minute * 60 + r.second for r in dorm_male]  # 把每一个时间点换算成秒
        ave_time_male = sum(time_male) / len(time_male)
        a = sum(time_male)

    ave_time_male = ave_time_male // 60  # 把秒换算成分钟
    ave_time_male = ave_time_male // 60  # 把分钟换算成小时

    dorm_female = list(Dorm.objects.filter(DateTime__gte=start_date, DateTime__lte=end_date, basic__School=school,
                                           basic__Gender='0').values_list('DateTime', flat=True))
    if len(dorm_female) == 0:
        ave_time_female = 0
        b=0
    else:
        time_female = [r.hour * 3600 + r.minute * 60 + r.second for r in dorm_female]
        ave_time_female = sum(time_female) / len(time_female)
        b = sum(time_female)
    ave_time_female = ave_time_female // 60  # 把秒换算成分钟
    ave_time_female = ave_time_female // 60  # 把分钟换算成小时

    if len(dorm_all) == 0:
        ave_time = 0
    else:
        ave_time=(a+b)/len(dorm_all)
    ave_time=ave_time // 60     #把秒换算成分钟
    ave_time=ave_time // 60    #把分钟换算成小时

    #消费分布
    #消费与性别
    #给Card表格加上外键,很慢，17万条数据估计要几个小时
    #可以建立一个中间表格，记录每个人一学期的总消费，或者每个月的平均消费
    '''
    re=Card.objects.all()
    i=1
    for r in re:
        print(i)
        i=i+1
        if r.basic is None:
            tmp=Basic.objects.filter(StuID=r.StuID)
            if tmp.count() >0:
                Card.objects.filter(StuID = r.StuID).update(StuID=r.StuID)
    '''

    #用python的方法处理
    '''
    start_date=datetime.date(2016,7,1)
    end_date=datetime.date(2017,2,1)
    stulist=list(Basic.objects.filter(School=school).values_list('StuID','Gender'))
    cost_dis=[]
    if len(stulist) ==0:
        cost_dis=[1,1,1,1,1]
        ave_cost_male=0
        ave_cost_female=0
    else:
        x=[0,100,200,300,400,500]
        ave_cost = [Card.objects.filter(StuID = stu[0], DateTime__gte=start_date, DateTime__lte=end_date, Cost__lt=0).aggregate(Sum("Cost")) for stu in stulist] #每个人的平均消费
        tmp=[]
        for c in ave_cost:
            if not c['Cost__sum'] is None:
                tmp.append(-c['Cost__sum']/5)
            else:
                tmp.append(0)
        ave_cost=tmp
        i=1
        while i <= 5:
            if i==5:
                cost_dis.append(sum(x[i]>=c>=x[i-1] for c in ave_cost))
            else:
                cost_dis.append(sum(x[i]>c>=x[i-1] for c in ave_cost))
            i=i+1

        a=[ave_cost[i] for i in range(len(ave_cost)) if stulist[i][1] == '1' and ave_cost[i]!=0]
        if len(a)==0:
            ave_cost_male=0
        else:
            ave_cost_male=sum(a)/len(a)

        b=[ave_cost[i] for i in range(len(ave_cost)) if stulist[i][1] == '0'and ave_cost[i]!=0]
        if len(b)==0:
            ave_cost_female=0
        else:
            ave_cost_female=sum(b)/len(b)

        ave_cost = sum(ave_cost)/(len(a)+len(b))
        '''
    #python的方法处理，只考虑10个学生
    start_date=datetime.date(2016,7,1)
    end_date=datetime.date(2017,2,1)
    stulist=list(Basic.objects.filter(School=school).values_list('StuID','Gender'))
    cost_dis=[]
    if len(stulist) ==0:
        cost_dis=[1,1,1,1,1]
        ave_cost_male=0
        ave_cost_female=0
    else:
        u=25
        x=[0,100,200,300,400,500]
        ave_cost = [Card.objects.filter(StuID = stu[0], DateTime__gte=start_date, DateTime__lte=end_date, Cost__lt=0).aggregate(Sum("Cost")) for stu in stulist[1:u]] #每个人的平均消费
        tmp=[]
        for c in ave_cost:
            if not c['Cost__sum'] is None:
                tmp.append(-c['Cost__sum']/5)
            else:
                tmp.append(0)
        ave_cost=tmp
        i=1
        while i <= 5:
            if i==5:
                cost_dis.append(sum(x[i]>=c>=x[i-1] for c in ave_cost))
            else:
                cost_dis.append(sum(x[i]>c>=x[i-1] for c in ave_cost))
            i=i+1

        a=[ave_cost[i] for i in range(len(ave_cost)) if stulist[i][1] == '1' and ave_cost[i]!=0]
        if len(a)==0:
            ave_cost_male=0
        else:
            ave_cost_male=sum(a)/len(a)

        b=[ave_cost[i] for i in range(len(ave_cost)) if stulist[i][1] == '0'and ave_cost[i]!=0]
        if len(b)==0:
            ave_cost_female=0
        else:
            ave_cost_female=sum(b)/len(b)

        ave_cost = sum(ave_cost)/(len(a)+len(b))

    '''
    #用数据库的方法处理
    ave_cost=list(Basic.objects.filter(School=school, card__DateTime__gte=start_date, card__DateTime__lte=end_date, card__Cost__lte=0).annotate(Sum("card__Cost")).values_list('card__Cost', flat=True))
    print(ave_cost)
    x=[0,100,200,300,400,500]
    cost_dis=[]
    i=1
    while i <= 5:
        if i==5:
            print(i)
            cost_dis.append(sum(x[i]>=-c['Cost__sum']/17>=x[i-1] for c in ave_cost if not c['Cost__sum'] is None))
        else:
            print(i)
            cost_dis.append(sum(x[i]>-c['Cost__sum']/17>=x[i-1] for c in ave_cost if not c['Cost__sum'] is None))
        i=i+1
    '''

    #图书馆访问
    #之前用数据库方法，其实不对，因为我只考虑了cost等table里有的stuID，其实应该先把全班的stuID查出来
    start_date=datetime.date(2016,7,1)
    end_date=datetime.date(2017,2,1)
    stulist=list(Basic.objects.filter(School=school).values_list('StuID','Gender'))

    if len(stulist) ==0:
        visit_dis=[1,1,1,1,1]
        ave_visit_male=0
        ave_visit_female=0
    else:
        x=[0,20,40,60,80,100]
        ave_visit = [Lib.objects.filter(StuID = stu[0], DateTime__gte=start_date, DateTime__lte=end_date).aggregate(c=Count("id"))['c'] for stu in stulist] #每个人的平均消费
        i=1
        visit_dis=[]
        while i <= 5:
            if i==5:
                visit_dis.append(sum(x[i]>=c>=x[i-1] for c in ave_visit))
            else:
                visit_dis.append(sum(x[i]>c>=x[i-1] for c in ave_visit))
            i=i+1

        a=[ave_visit[i] for i in range(len(ave_visit)) if stulist[i][1] == '1']
        if len(a)==0:
            ave_visit_male=0
        else:
            ave_visit_male=sum(a)/len(a)

        b=[ave_visit[i] for i in range(len(ave_visit)) if stulist[i][1] == '0']
        if len(b)==0:
            ave_visit_female=0
        else:
            ave_visit_female=sum(b)/len(b)

        ave_visit = sum(ave_visit)/(len(a)+len(b))


    #借书
    start_date=datetime.date(2016,7,1)
    end_date=datetime.date(2017,2,1)
    stulist=list(Basic.objects.filter(School=school).values_list('StuID','Gender'))

    if len(stulist) ==0:
        book_dis=[1,1,1,1,1]
        ave_book_male=0
        ave_book_female=0
    else:
        x=[0,20,40,60,80,100]
        ave_book = [Book.objects.filter(StuID = stu[0], Date__gte=start_date, Date__lte=end_date).aggregate(c=Count("id"))['c'] for stu in stulist] #每个人一学期的借书总数
        i=1
        book_dis=[]
        while i <= 5:
            if i==5:
                book_dis.append(sum(x[i]>=c>=x[i-1] for c in ave_book))
            else:
                book_dis.append(sum(x[i]>c>=x[i-1] for c in ave_book))
            i=i+1

        a=[ave_book[i] for i in range(len(ave_book)) if stulist[i][1] == '1']
        if len(a)==0:
            ave_book_male=0
        else:
            ave_book_male=sum(a)/len(a)

        b=[ave_book[i] for i in range(len(ave_book)) if stulist[i][1] == '0']
        if len(b)==0:
            ave_book_female=0
        else:
            ave_book_female=sum(b)/len(b)

        ave_book = sum(ave_book)/(len(a)+len(b))


    #借书，图书馆访问和消费分布的代码一模一样，可以抽取成函数
    ret = {'cdfall':cdfall, 'pdfall':pdfall, 'num':num,
           'ave_score_female':ave_score_female, 'ave_score_male':ave_score_male, 'ave_score':ave_score,
           'score_lib_ave':score_lib_ave, 'score_lib_max':score_lib_max, 'score_lib_min':score_lib_min,
           'score_dormtime_ave':score_dormtime_ave, 'score_dormtime_max':score_dormtime_max, 'score_dormtime_min':score_dormtime_min,
           'health_num':health_num,
           'ave_health_score_male':ave_health_score_male, 'ave_health_score_female':ave_health_score_female, 'ave_health_score':ave_health_score,
           'health_dormtime_ave':health_dormtime_ave, 'health_dormtime_max':health_dormtime_max, 'health_dormtime_min':health_dormtime_min,
           'province_num':province_num,'score_province':score_province,
           'dorm_num':dorm_num,
           'ave_time_female':ave_time_female, 'ave_time_male':ave_time_male, 'ave_time':ave_time,
           'cost_dis':cost_dis, 'ave_cost_male':ave_cost_male, 'ave_cost_female':ave_cost_female, 'ave_cost':ave_cost,
           'visit_dis':visit_dis, 'ave_visit_male':ave_visit_male, 'ave_visit_female':ave_visit_female, 'ave_visit':ave_visit,
           'book_dis':book_dis, 'ave_book_male':ave_book_male, 'ave_book_female':ave_book_female, 'ave_book':ave_book,
           'hos_dis':hos_dis, 'ave_hos_male':ave_hos_male, 'ave_hos_female':ave_hos_female, 'ave_hos':ave_hos,
           'hos_health_min':hos_health_min, 'hos_health_max':hos_health_max, 'hos_health':hos_health}

    return HttpResponse(json.dumps(ret), content_type='application/json')



def inquiry_initial(school):
    time = '20151'
    start_date = datetime.date(2016, 9, 1)
    end_date = datetime.date(2017, 2, 1)
    score_all = list(Score.objects.filter(Semester=time, School=school).values_list('AveScore', flat=True))

    # geo_distribution
    r = list(Basic.objects.filter(School=school).values_list('Province', flat=True))
    province = ['四川', '江西', '江苏', '山东', '安徽', '上海', '重庆', '福建', '河南', '河北', '广东', '广西', '山西', '天津', '湖北', '浙江', '陕西',
                '内蒙古', '海南',
                '辽宁', '吉林', '黑龙江', '湖南', '贵州', '云南', '甘肃', '青海', '台湾', '北京', '西藏', '宁夏', '新疆', '香港', '澳门']
    province_num = {}
    for pro in province:
        province_num[pro] = sum(pro in s for s in r)

    r = list(Score.objects.filter(Semester=time, School=school).values_list('basic__Province', 'AveScore'))
    score_province = {}
    for pro in province:
        a = [float(s[1]) for s in r if pro in s[0]]
        if len(a) == 0:
            score_province[pro] = 0
        else:
            score_province[pro] = sum(a) / len(a)

    # grades
    if len(score_all)==0:
        cdfall=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    else:
        x = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        cdfall = []
        for i in x:
            cdfall.append(sum(float(j) < i for j in score_all) / len(score_all))

    if len(score_all)==0:
        cdfall=[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    else:
        x = [-10, 0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110]
        pdfall = []
        i = 1
        while i <= 11:
            pdfall.append(sum((x[i - 1] + x[i]) / 2 < float(j) < (x[i] + x[i + 1]) / 2 for j in score_all) / len(score_all))
            i = i + 1

    x = [0, 50, 60, 70, 80, 90, 100]
    num = []
    i = 1
    while i <= 6:
        if i == 6:
            num.append(sum(x[i - 1] <= float(j) <= x[i] for j in score_all))
        else:
            num.append(sum(x[i - 1] <= float(j) < x[i] for j in score_all))
        i = i + 1

    # the average grade for different gender
    score_male = list(
        Score.objects.filter(Semester=time, School=school, basic__Gender='1').values_list('AveScore', flat=True))
    if len(score_male) == 0:
        ave_score_male = 0
    else:
        ave_score_male = sum(float(j) for j in score_male) / len(score_male)

    score_female = list(
        Score.objects.filter(Semester=time, School=school, basic__Gender='0').values_list('AveScore', flat=True))
    if len(score_female)==0:
        ave_score_female = 0
    else:
        ave_score_female = sum(float(j) for j in score_female) / len(score_female)

    if len(score_all) ==0:
        ave_score = 0
    else:
        ave_score = sum(float(j) for j in score_all) / len(score_all)


    # score vs. library
    r = Basic.objects.filter(School=school, score__Semester=time, lib__DateTime__gte=start_date,
                             lib__DateTime__lte=end_date).annotate(count=Count("lib__id")).values('count',
                                                                                                  'score__AveScore')
    score_lib_ave = []
    score_lib_max = []
    score_lib_min = []
    x = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]
    i = 1
    while i <= 9:
        if i == 9:
            re = r.filter(count__gte=x[i - 1], count__lte=x[i])
            if re.count() == 0:
                score_lib_ave.append(0)
                score_lib_max.append(0)
                score_lib_min.append(0)
            else:
                score_lib_ave.append(r.filter(count__gte=x[i - 1], count__lte=x[i]).aggregate(Avg("score__AveScore"))[
                                         'score__AveScore__avg'])
                score_lib_max.append(r.filter(count__gte=x[i - 1], count__lte=x[i]).aggregate(Max("score__AveScore"))[
                                         'score__AveScore__max'])
                score_lib_min.append(r.filter(count__gte=x[i - 1], count__lte=x[i]).aggregate(Min("score__AveScore"))[
                                         'score__AveScore__min'])
        else:
            re = r.filter(count__gte=x[i - 1], count__lt=x[i])
            if re.count() == 0:
                score_lib_ave.append(0)
                score_lib_max.append(0)
                score_lib_min.append(0)
            else:
                score_lib_ave.append(r.filter(count__gte=x[i - 1], count__lte=x[i]).aggregate(Avg("score__AveScore"))[
                                         'score__AveScore__avg'])
                score_lib_max.append(r.filter(count__gte=x[i - 1], count__lte=x[i]).aggregate(Max("score__AveScore"))[
                                         'score__AveScore__max'])
                score_lib_min.append(r.filter(count__gte=x[i - 1], count__lte=x[i]).aggregate(Min("score__AveScore"))[
                                         'score__AveScore__min'])
        i = i + 1

    # score vs. dorm
    start_date = datetime.date(2015, 10, 1)
    end_date = datetime.date(2017, 2, 1)
    # 其实应该算一下每个人的平均回寝时间，存在一张表中，再算;这里为了方便，用了一个近似的算法
    r = list(Basic.objects.filter(School=school, score__Semester=time, dorm__DateTime__gte=start_date,
                                  dorm__DateTime__lte=end_date).values_list('dorm__DateTime', 'score__AveScore'))
    x = [0, 6, 12, 15, 18, 21, 22, 23]
    i = 1
    score_dormtime_ave = []
    score_dormtime_max = []
    score_dormtime_min = []
    while i <= 7:
        if i == 7:
            re = [float(tmp[1]) for tmp in r if x[i] >= tmp[0].hour >= x[i - 1]]
            if len(re) > 0:
                score_dormtime_ave.append(sum(re) / len(re))
                score_dormtime_max.append(max(re))
                score_dormtime_min.append(min(re))
            else:
                score_dormtime_ave.append(0)
                score_dormtime_max.append(0)
                score_dormtime_min.append(0)
        else:
            re = [float(tmp[1]) for tmp in r if x[i] > tmp[0].hour >= x[i - 1]]
            if len(re) > 0:
                score_dormtime_ave.append(sum(re) / len(re))
                score_dormtime_max.append(max(re))
                score_dormtime_min.append(min(re))
            else:
                score_dormtime_ave.append(0)
                score_dormtime_max.append(0)
                score_dormtime_min.append(0)
        i = i + 1

    # health
    # physical test
    # distribution
    health_score_all = list(Health.objects.filter(Semester=2016, School=school).values_list('TotalScore', flat=True))
    x = [0, 50, 60, 70, 80, 90, 100]
    health_num = getdistribution(x, health_score_all)

    # 体质测试与性别
    health_score_male = list(
        Health.objects.filter(Semester=2016, School=school, basic__Gender='1').values_list('TotalScore', flat=True))
    if len(health_score_male) ==0:
        ave_health_score_male = 0
    else:
        ave_health_score_male = sum(float(j) for j in health_score_male) / len(health_score_male)

    health_score_female = list(
        Health.objects.filter(Semester=2016, School=school, basic__Gender='0').values_list('TotalScore', flat=True))
    if len(health_score_female) ==0:
        ave_health_score_female = 0
    else:
        ave_health_score_female = sum(float(j) for j in health_score_female) / len(health_score_female)

    if len(health_score_all) == 0:
        ave_health_score = 0
    else:
        ave_health_score = sum(float(j) for j in health_score_all) / len(health_score_all)




    # 体质与回寝时间
    start_date = datetime.date(2015, 10, 1)
    end_date = datetime.date(2017, 2, 1)
    # 其实应该算一下每个人的平均回寝时间，存在一张表中，再算;这里为了方便，用了一个近似的算法
    # 这里回寝时间多次用到，可以抽取出来
    # 也可以给每个表格加上school和gender属性，就不用join了
    # dorm表格和health表格也可以建立多对多的外键
    r = list(Basic.objects.filter(School=school, health__Semester=2016, dorm__DateTime__gte=start_date,
                                  dorm__DateTime__lte=end_date).values_list('dorm__DateTime', 'health__TotalScore'))
    x = [0, 6, 12, 15, 18, 21, 22, 23]
    i = 1
    health_dormtime_ave = []
    health_dormtime_max = []
    health_dormtime_min = []
    while i <= 7:
        if i == 7:
            re = [float(tmp[1]) for tmp in r if x[i] >= tmp[0].hour >= x[i - 1]]
            if len(re) > 0:
                health_dormtime_ave.append(sum(re) / len(re))
                health_dormtime_max.append(max(re))
                health_dormtime_min.append(min(re))
            else:
                health_dormtime_ave.append(0)
                health_dormtime_max.append(0)
                health_dormtime_min.append(0)
        else:
            re = [float(tmp[1]) for tmp in r if x[i] > tmp[0].hour >= x[i - 1]]
            if len(re) > 0:
                health_dormtime_ave.append(sum(re) / len(re))
                health_dormtime_max.append(max(re))
                health_dormtime_min.append(min(re))
            else:
                health_dormtime_ave.append(0)
                health_dormtime_max.append(0)
                health_dormtime_min.append(0)
        i = i + 1

    # hospital
    # 去校医院次数分布
    # 去校医院次数与性别
    # 去校医院次数与体质
    start_date=datetime.date(2016,7,1)
    end_date=datetime.date(2017,2,1)
    stulist=list(Basic.objects.filter(School=school).values_list('StuID','Gender'))

    if len(stulist) ==0:
        hos_dis=[1,1,1,1,1]
        ave_hos_male=0
        ave_hos_female=0
    else:
        x=[0, 10, 20, 30, 40, 50]
        ave_hos = [HosReg.objects.filter(StuID = stu[0], DateTime__gte=start_date, DateTime__lte=end_date).aggregate(c=Count("id"))['c'] for stu in stulist] #每个人一学期去校医院总次数
        i=1
        hos_dis=[]
        while i <= 5:
            if i==5:
                hos_dis.append(sum(x[i]>=c>=x[i-1] for c in ave_hos))
            else:
                hos_dis.append(sum(x[i]>c>=x[i-1] for c in ave_hos))
            i=i+1
        #性别
        a=[ave_hos[i] for i in range(len(ave_hos)) if stulist[i][1] == '1']
        if len(a)==0:
            ave_hos_male=0
        else:
            ave_hos_male=sum(a)/len(a)

        b=[ave_hos[i] for i in range(len(ave_hos)) if stulist[i][1] == '0']
        if len(b)==0:
            ave_hos_female=0
        else:
            ave_hos_female=sum(b)/len(b)
        ave_hos = sum(ave_hos)/(len(a)+len(b))




    #去校医院次数与体质
    stulist=list(Basic.objects.filter(School=school, health__Semester = 2016).values_list('StuID','health__TotalScore'))
    if len(stulist) ==0:
        hos_health=[0,0,0,0,0,0,0,0,0,0]
        hos_health_max=[0,0,0,0,0,0,0,0,0,0]
        hos_health_min=[0,0,0,0,0,0,0,0,0,0]
    else:
        x=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        hos = [HosReg.objects.filter(StuID = stu[0], DateTime__gte=start_date, DateTime__lte=end_date).aggregate(c=Count("id"))['c'] for stu in stulist] #每个人一学期去校医院总次数
        i=1
        hos_health=[]
        hos_health_min=[]
        hos_health_max=[]
        while i <= 10:
            if i==10:
                a=[float(hos[j]) for j in range(len(hos)) if x[i]>=float(stulist[j][1])>=x[i-1]]
                if len(a)==0:
                    hos_health.append(0)
                    hos_health_min.append(0)
                    hos_health_max.append(0)
                else:
                    hos_health.append(sum(a)/len(a))
                    hos_health_min.append(max(a))
                    hos_health_max.append(min(a))
            else:
                a=[float(hos[j]) for j in range(len(hos)) if x[i]>float(stulist[j][1])>=x[i-1]]
                if len(a)==0:
                    hos_health.append(0)
                    hos_health_min.append(0)
                    hos_health_max.append(0)
                else:
                    hos_health.append(sum(a)/len(a))
                    hos_health_min.append(max(a))
                    hos_health_max.append(min(a))
            i=i+1


    # 校园生活
    # 回寝时间分布
    start_date = datetime.date(2015, 10, 1)
    end_date = datetime.date(2017, 2, 1)
    dorm_all = list(
        Dorm.objects.filter(basic__School=school, DateTime__gte=start_date, DateTime__lte=end_date).values_list(
            'DateTime', flat=True))

    x = [0, 6, 12, 18, 22, 24]
    dorm_num = []
    i = 1
    while i <= 5:
        if i == 5:
            dorm_num.append(sum(x[i] >= r.hour >= x[i - 1] for r in dorm_all))
        else:
            dorm_num.append(sum(x[i] > r.hour >= x[i - 1] for r in dorm_all))
        i = i + 1

    # 回寝时间与性别
    dorm_male = list(Dorm.objects.filter(DateTime__gte=start_date, DateTime__lte=end_date, basic__School=school,
                                         basic__Gender='1').values_list('DateTime', flat=True))
    if len(dorm_male) == 0:
        ave_time_male = 0
        a=0
    else:
        time_male = [r.hour * 3600 + r.minute * 60 + r.second for r in dorm_male]  # 把每一个时间点换算成秒
        ave_time_male = sum(time_male) / len(time_male)
        a = sum(time_male)

    ave_time_male = ave_time_male // 60  # 把秒换算成分钟
    ave_time_male = ave_time_male // 60  # 把分钟换算成小时

    dorm_female = list(Dorm.objects.filter(DateTime__gte=start_date, DateTime__lte=end_date, basic__School=school,
                                           basic__Gender='0').values_list('DateTime', flat=True))
    if len(dorm_female) == 0:
        ave_time_female = 0
        b=0
    else:
        time_female = [r.hour * 3600 + r.minute * 60 + r.second for r in dorm_female]
        ave_time_female = sum(time_female) / len(time_female)
        b = sum(time_female)
    ave_time_female = ave_time_female // 60  # 把秒换算成分钟
    ave_time_female = ave_time_female // 60  # 把分钟换算成小时

    if len(dorm_all) == 0:
        ave_time = 0
    else:
        ave_time=(a+b)/len(dorm_all)
    ave_time=ave_time // 60     #把秒换算成分钟
    ave_time=ave_time // 60    #把分钟换算成小时

    #消费分布
    #消费与性别
    #给Card表格加上外键,很慢，17万条数据估计要几个小时
    #可以建立一个中间表格，记录每个人一学期的总消费，或者每个月的平均消费
    '''
    re=Card.objects.all()
    i=1
    for r in re:
        print(i)
        i=i+1
        if r.basic is None:
            tmp=Basic.objects.filter(StuID=r.StuID)
            if tmp.count() >0:
                Card.objects.filter(StuID = r.StuID).update(StuID=r.StuID)
    '''

    #用python的方法处理
    '''
    start_date=datetime.date(2016,7,1)
    end_date=datetime.date(2017,2,1)
    stulist=list(Basic.objects.filter(School=school).values_list('StuID','Gender'))
    cost_dis=[]
    if len(stulist) ==0:
        cost_dis=[1,1,1,1,1]
        ave_cost_male=0
        ave_cost_female=0
    else:
        x=[0,100,200,300,400,500]
        ave_cost = [Card.objects.filter(StuID = stu[0], DateTime__gte=start_date, DateTime__lte=end_date, Cost__lt=0).aggregate(Sum("Cost")) for stu in stulist] #每个人的平均消费
        tmp=[]
        for c in ave_cost:
            if not c['Cost__sum'] is None:
                tmp.append(-c['Cost__sum']/5)
            else:
                tmp.append(0)
        ave_cost=tmp
        i=1
        while i <= 5:
            if i==5:
                cost_dis.append(sum(x[i]>=c>=x[i-1] for c in ave_cost))
            else:
                cost_dis.append(sum(x[i]>c>=x[i-1] for c in ave_cost))
            i=i+1

        a=[ave_cost[i] for i in range(len(ave_cost)) if stulist[i][1] == '1' and ave_cost[i]!=0]
        if len(a)==0:
            ave_cost_male=0
        else:
            ave_cost_male=sum(a)/len(a)

        b=[ave_cost[i] for i in range(len(ave_cost)) if stulist[i][1] == '0'and ave_cost[i]!=0]
        if len(b)==0:
            ave_cost_female=0
        else:
            ave_cost_female=sum(b)/len(b)

        ave_cost = sum(ave_cost)/(len(a)+len(b))
        '''
    #python的方法处理，只考虑10个学生
    start_date=datetime.date(2016,7,1)
    end_date=datetime.date(2017,2,1)
    stulist=list(Basic.objects.filter(School=school).values_list('StuID','Gender'))
    cost_dis=[]
    if len(stulist) ==0:
        cost_dis=[1,1,1,1,1]
        ave_cost_male=0
        ave_cost_female=0
    else:
        u=25
        x=[0,100,200,300,400,500]
        ave_cost = [Card.objects.filter(StuID = stu[0], DateTime__gte=start_date, DateTime__lte=end_date, Cost__lt=0).aggregate(Sum("Cost")) for stu in stulist[1:u]] #每个人的平均消费
        tmp=[]
        for c in ave_cost:
            if not c['Cost__sum'] is None:
                tmp.append(-c['Cost__sum']/5)
            else:
                tmp.append(0)
        ave_cost=tmp
        i=1
        while i <= 5:
            if i==5:
                cost_dis.append(sum(x[i]>=c>=x[i-1] for c in ave_cost))
            else:
                cost_dis.append(sum(x[i]>c>=x[i-1] for c in ave_cost))
            i=i+1

        a=[ave_cost[i] for i in range(len(ave_cost)) if stulist[i][1] == '1' and ave_cost[i]!=0]
        if len(a)==0:
            ave_cost_male=0
        else:
            ave_cost_male=sum(a)/len(a)

        b=[ave_cost[i] for i in range(len(ave_cost)) if stulist[i][1] == '0'and ave_cost[i]!=0]
        if len(b)==0:
            ave_cost_female=0
        else:
            ave_cost_female=sum(b)/len(b)

        ave_cost = sum(ave_cost)/(len(a)+len(b))

    '''
    #用数据库的方法处理
    ave_cost=list(Basic.objects.filter(School=school, card__DateTime__gte=start_date, card__DateTime__lte=end_date, card__Cost__lte=0).annotate(Sum("card__Cost")).values_list('card__Cost', flat=True))
    print(ave_cost)
    x=[0,100,200,300,400,500]
    cost_dis=[]
    i=1
    while i <= 5:
        if i==5:
            print(i)
            cost_dis.append(sum(x[i]>=-c['Cost__sum']/17>=x[i-1] for c in ave_cost if not c['Cost__sum'] is None))
        else:
            print(i)
            cost_dis.append(sum(x[i]>-c['Cost__sum']/17>=x[i-1] for c in ave_cost if not c['Cost__sum'] is None))
        i=i+1
    '''

    #图书馆访问
    #之前用数据库方法，其实不对，因为我只考虑了cost等table里有的stuID，其实应该先把全班的stuID查出来
    start_date=datetime.date(2016,7,1)
    end_date=datetime.date(2017,2,1)
    stulist=list(Basic.objects.filter(School=school).values_list('StuID','Gender'))

    if len(stulist) ==0:
        visit_dis=[1,1,1,1,1]
        ave_visit_male=0
        ave_visit_female=0
    else:
        x=[0,20,40,60,80,100]
        ave_visit = [Lib.objects.filter(StuID = stu[0], DateTime__gte=start_date, DateTime__lte=end_date).aggregate(c=Count("id"))['c'] for stu in stulist] #每个人的平均消费
        i=1
        visit_dis=[]
        while i <= 5:
            if i==5:
                visit_dis.append(sum(x[i]>=c>=x[i-1] for c in ave_visit))
            else:
                visit_dis.append(sum(x[i]>c>=x[i-1] for c in ave_visit))
            i=i+1

        a=[ave_visit[i] for i in range(len(ave_visit)) if stulist[i][1] == '1']
        if len(a)==0:
            ave_visit_male=0
        else:
            ave_visit_male=sum(a)/len(a)

        b=[ave_visit[i] for i in range(len(ave_visit)) if stulist[i][1] == '0']
        if len(b)==0:
            ave_visit_female=0
        else:
            ave_visit_female=sum(b)/len(b)

        ave_visit = sum(ave_visit)/(len(a)+len(b))


    #借书
    start_date=datetime.date(2016,7,1)
    end_date=datetime.date(2017,2,1)
    stulist=list(Basic.objects.filter(School=school).values_list('StuID','Gender'))

    if len(stulist) ==0:
        book_dis=[1,1,1,1,1]
        ave_book_male=0
        ave_book_female=0
    else:
        x=[0,20,40,60,80,100]
        ave_book = [Book.objects.filter(StuID = stu[0], Date__gte=start_date, Date__lte=end_date).aggregate(c=Count("id"))['c'] for stu in stulist] #每个人一学期的借书总数
        i=1
        book_dis=[]
        while i <= 5:
            if i==5:
                book_dis.append(sum(x[i]>=c>=x[i-1] for c in ave_book))
            else:
                book_dis.append(sum(x[i]>c>=x[i-1] for c in ave_book))
            i=i+1

        a=[ave_book[i] for i in range(len(ave_book)) if stulist[i][1] == '1']
        if len(a)==0:
            ave_book_male=0
        else:
            ave_book_male=sum(a)/len(a)

        b=[ave_book[i] for i in range(len(ave_book)) if stulist[i][1] == '0']
        if len(b)==0:
            ave_book_female=0
        else:
            ave_book_female=sum(b)/len(b)

        ave_book = sum(ave_book)/(len(a)+len(b))


    #借书，图书馆访问和消费分布的代码一模一样，可以抽取成函数
    ret = {'cdfall':cdfall, 'pdfall':pdfall, 'num':num,
           'ave_score_female':ave_score_female, 'ave_score_male':ave_score_male, 'ave_score':ave_score,
           'score_lib_ave':score_lib_ave, 'score_lib_max':score_lib_max, 'score_lib_min':score_lib_min,
           'score_dormtime_ave':score_dormtime_ave, 'score_dormtime_max':score_dormtime_max, 'score_dormtime_min':score_dormtime_min,
           'health_num':health_num,
           'ave_health_score_male':ave_health_score_male, 'ave_health_score_female':ave_health_score_female, 'ave_health_score':ave_health_score,
           'health_dormtime_ave':health_dormtime_ave, 'health_dormtime_max':health_dormtime_max, 'health_dormtime_min':health_dormtime_min,
           'province_num':province_num,'score_province':score_province,
           'dorm_num':dorm_num,
           'ave_time_female':ave_time_female, 'ave_time_male':ave_time_male, 'ave_time':ave_time,
           'cost_dis':cost_dis, 'ave_cost_male':ave_cost_male, 'ave_cost_female':ave_cost_female, 'ave_cost':ave_cost,
           'visit_dis':visit_dis, 'ave_visit_male':ave_visit_male, 'ave_visit_female':ave_visit_female, 'ave_visit':ave_visit,
           'book_dis':book_dis, 'ave_book_male':ave_book_male, 'ave_book_female':ave_book_female, 'ave_book':ave_book,
           'hos_dis':hos_dis, 'ave_hos_male':ave_hos_male, 'ave_hos_female':ave_hos_female, 'ave_hos':ave_hos,
           'hos_health_min':hos_health_min, 'hos_health_max':hos_health_max, 'hos_health':hos_health}
    return ret


def getdistribution(x, data):
    # x includes endpoints of intervals
    l = len(x)
    num = []
    i = 1
    while i <= len(x):
        if i == len(x):
            num.append(sum(x[i - 1] <= float(j) <= x[i] for j in data))
        else:
            num.append(sum(x[i - 1] <= float(j) < x[i] for j in data))
        i = i + 1
    return num


def base(request):
    return render(request, 'servermaterial/base.html')


def supervision(request):
    # 读取学院信息，显示在下拉框上
    school_query_list = Basic.objects.values('School')
    school_list = list(set([tmp['School'] for tmp in school_query_list if tmp['School'] != '']))

    for i in range(len(school_list)):
        if school_list[i]=='电子信息与电气工程学院':
            school_list[i]=school_list[0]
            school_list[0]='电子信息与电气工程学院'
            break

    major_query_list = Basic.objects.filter(School=school_list[0]).values('Major')
    major_list = list(set([tmp['Major'] for tmp in major_query_list if tmp['Major'] != '']))

    grade_query_list = Basic.objects.filter(School=school_list[0], Major=major_list[0]).values('Grade')
    grade_list = list(set([tmp['Grade'] for tmp in grade_query_list if tmp['Grade'] != '']))

    class_query_list = Basic.objects.filter(School=school_list[0], Major=major_list[0], Grade=grade_list[0]).values(
        'classNo')
    class_list = list(set([tmp['classNo'] for tmp in class_query_list if tmp['classNo'] != '']))


    return render(request, 'servermaterial/supervision_new_2.html', context={'school_list': school_list,
                                                                             'major_list': major_list,
                                                                             'grade_list': grade_list,
                                                                             'class_list': class_list})


def result(request):
    print('here')
    # Basic.objects.all().delete()
    # 读取学院信息，显示在下拉框上
    school_query_list = Basic.objects.values('School')
    school_list = list(set([tmp['School'] for tmp in school_query_list if tmp['School'] != '']))

    major_query_list = Basic.objects.filter(School=school_list[0]).values('Major')
    major_list = list(set([tmp['Major'] for tmp in major_query_list if tmp['Major'] != '']))

    grade_query_list = Basic.objects.filter(School=school_list[0], Major=major_list[0]).values('Grade')
    grade_list = list(set([tmp['Grade'] for tmp in grade_query_list if tmp['Grade'] != '']))

    class_query_list = Basic.objects.filter(School=school_list[0], Major=major_list[0], Grade=grade_list[0]).values(
        'classNo')
    class_list = list(set([tmp['classNo'] for tmp in class_query_list if tmp['classNo'] != '']))

    id_query_list = Basic.objects.filter(School=school_list[0], Major=major_list[0], Grade=grade_list[0],
                                         classNo=class_list[0]).values('StuID')
    id_list = list(set([tmp['StuID'] for tmp in id_query_list if tmp['StuID'] != '']))
    return render(request, 'servermaterial/result.html', context={'school_list': school_list,
                                                                  'major_list': major_list,
                                                                  'grade_list': grade_list,
                                                                  'class_list': class_list,
                                                                  'id_list': id_list})


##查询
def query(request):
    if request.method == 'POST':
        # 关键内容
        stuid = request.POST.get('stuid')
        # print(stuid)
        # 没有判空   应该加一个判断，若学号不存在，返回什么
        nowTime = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 现在
        print(nowTime)
        pastTime = (datetime.datetime.now() - datetime.timedelta(days=730)).strftime('%Y-%m-%d %H:%M:%S')  # 过去3年时间
        print(pastTime)

        """
        table
        """
        objs = Score.objects.filter(StuID=stuid)
        res1 = [obj.as_dict() for obj in objs]

        objs2 = Moral.objects.filter(StuID=stuid)
        res2 = [obj.as_dict() for obj in objs2]

        objs3 = Health.objects.filter(StuID=stuid)
        res3 = [obj.as_dict() for obj in objs3]

        objs4 = Basic.objects.filter(StuID=stuid)
        res4 = [obj.as_dict() for obj in objs4]
        if Basic.objects.filter(StuID=stuid):
            FinanceType = '无'
            if Finance.objects.filter(StuID=stuid):
                FinanceType = Finance.objects.filter(StuID=stuid)[0].FinanceType
            res4[0].update({'FinanceType': FinanceType})  # res4就一个字典元素

        ##为了下面的画像
        # print(res4)
        str12 = ""
        str13 = ""
        str14 = ""
        str15 = ""
        str16 = ""
        str17 = ""
        if res4.__len__() == 1:
            str12 = res4[0]["School"]
            str13 = res4[0]["Major"]
            str14 = res4[0]["classNo"] + "班"
            str15 = "来自" + res4[0]["Province"]
            str16 = res4[0]["Gender"]
            if res4[0]["FinanceType"] != "无":
                str17 = res4[0]["FinanceType"]

        objs = Aid.objects.filter(StuID=stuid)
        res9 = [obj.as_dict() for obj in objs]

        """
        chart 都没判空
        """
        xx = list(Score.objects.filter(StuID=stuid).values_list('Semester', flat=True))
        # print(xx)
        dd = []
        Grade = list(Score.objects.filter(StuID=stuid).values_list('Grade', flat=True))[0]
        str18 = str(int(Grade)) + "级"
        School = list(Score.objects.filter(StuID=stuid).values_list('School', flat=True))[0]
        for sem in xx:
            score = Score.objects.get(StuID=stuid, Semester=sem).AveScore
            score_ = list(
                Score.objects.filter(Semester=sem, Grade=Grade, School=School).values_list('AveScore', flat=True))
            numm = sum(float(score) >= float(j) for j in score_)
            dd.append(numm / len(score_))
        # print(dd)
        # ret1 = {'xx':xx, 'dd':dd}

        morallist = list(Moral.objects.filter(StuID=stuid).values_list('Semester', flat=True))
        xx2 = sorted(set(morallist), key=morallist.index)
        # print(xx2)
        dd2 = []
        for i in xx2:
            dd2.append(morallist.count(i))
        # print(dd2)

        xx3 = list(
            Health.objects.filter(StuID=stuid).values_list('Semester', flat=True))  # Grade and School donnot change
        # print(xx3)
        dd3 = []
        for sem in xx3:
            score = Health.objects.get(StuID=stuid, Semester=sem).TotalScore
            score_ = list(
                Health.objects.filter(Semester=sem, Grade=Grade, School=School).values_list('TotalScore', flat=True))
            numm = sum(float(score) >= float(j) for j in score_)
            dd3.append(numm / len(score_))
        # print(dd3)

        ###访问lib
        dd5 = []
        ccc = 0  # 为了画像
        dtlist = list(Lib.objects.filter(StuID=stuid).values_list('DateTime', flat=True))
        print(dtlist)
        Tdelta = (datetime.datetime.strptime(pastTime, '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime('2017-02-20',
                                                                                                         '%Y-%m-%d')).days + 1  ###代替126
        if len(dtlist) != 0:
            nlist = np.zeros(Tdelta)
            for item in dtlist:
                nitem = item.replace(tzinfo=None)
                # nitem = datetime.datetime.strptime(item, '%Y-%m-%d %H:%M:%S')
                # if datetime.datetime.strptime('2017-02-20 00:00:00', '%Y-%m-%d %H:%M:%S') <= nitem <= datetime.datetime.strptime('2017-06-25 23:59:59', '%Y-%m-%d %H:%M:%S'):
                if datetime.datetime.strptime('2017-02-20 00:00:00',
                                              '%Y-%m-%d %H:%M:%S') <= nitem <= datetime.datetime.strptime(pastTime,
                                                                                                          '%Y-%m-%d %H:%M:%S'):
                    delta = (nitem - datetime.datetime.strptime('2017-02-20', '%Y-%m-%d')).days
                    nlist[delta] += 1
            # print(nlist)
            for i in range(Tdelta):
                dd5.append([i + 1, nlist[i]])
            # print(dd5)
            nlist = list(nlist)
            ccc = Tdelta - nlist.count(0)
        print('ok')

        ###访问dorm
        dd6 = []
        dtlist = list(Dorm.objects.filter(StuID=stuid).values_list('DateTime', flat=True))
        if len(dtlist) != 0:
            nlist = np.zeros(Tdelta)
            for item in dtlist:
                nitem = item.replace(tzinfo=None)
                # nitem = datetime.datetime.strptime(item, '%Y-%m-%d %H:%M:%S.000000')
                if datetime.datetime.strptime('2017-02-20 00:00:00',
                                              '%Y-%m-%d %H:%M:%S') <= nitem <= datetime.datetime.strptime(pastTime,
                                                                                                          '%Y-%m-%d %H:%M:%S'):
                    delta = (nitem - datetime.datetime.strptime('2017-02-20', '%Y-%m-%d')).days
                    nlist[delta] += 1
            # print(nlist)
            for i in range(Tdelta):
                dd6.append([i + 1, nlist[i]])
            # print(dd6)

        ###消费
        dd7 = []
        dtlist = list(Card.objects.filter(StuID=stuid).values_list('DateTime', flat=True))
        costlist = list(Card.objects.filter(StuID=stuid).values_list('Cost', flat=True))
        totlcos = 0
        if len(dtlist) != 0:
            nlist = np.zeros(Tdelta)
            for item in range(len(dtlist)):
                nitem = datetime.datetime.strptime(dtlist[item], '%Y-%m-%d %H:%M:%S').replace(tzinfo=None)
                if datetime.datetime.strptime('2017-02-20 00:00:00',
                                              '%Y-%m-%d %H:%M:%S') <= nitem <= datetime.datetime.strptime(pastTime,
                                                                                                          '%Y-%m-%d %H:%M:%S'):
                    delta = (nitem - datetime.datetime.strptime('2017-02-20', '%Y-%m-%d')).days
                    if float(costlist[item]) < 0:
                        nlist[delta] += float(costlist[item])
                        totlcos += float(costlist[item])
            # print(nlist)
            for i in range(Tdelta):
                dd7.append([i + 1, nlist[i]])
            # print(dd7)
            # print(totlcos)

        xx8mid = []
        aidlist = Aid.objects.filter(StuID=stuid)
        for i in range(len(aidlist)):
            if aidlist[i].Aid != '':
                xx8mid.append(aidlist[i].Year)
            if aidlist[i].Scholorship != '':
                xx8mid.append(aidlist[i].Year)
        xx8 = sorted(set(xx8mid), key=xx8mid.index)
        # print(xx2)
        dd8 = []
        for i in xx8:
            dd8.append(xx8mid.count(i))
        # print(dd2)

        ###画像
        str0 = str(stuid)
        ##学业
        str1 = ""
        str11 = ""
        if Score.objects.filter(StuID=stuid):
            lis = list(Score.objects.filter(StuID=stuid))
            scoreO = lis[-1]
            if (float(scoreO.AveScore) <= 65.) or (int(scoreO.Low60) > 0) or (int(scoreO.Num0) > 0):
                str1 = "学业需要特别照顾"

            ascore = list(Score.objects.filter(StuID=stuid).values_list('AveScore', flat=True))
            ascore = list(map(float, ascore))
            # print(ascore)
            ascoree = np.mean(ascore)  # 平均成绩
            str11 = "累计平均成绩" + str(("%.2f" % ascoree))
            stulist = list(Score.objects.filter(Grade=Grade, School=School).values_list('StuID', flat=True))
            stulist = sorted(set(stulist), key=stulist.index)
            # print(stulist)
            stuscorlist = []
            for stu in stulist:
                ascore_ = list(Score.objects.filter(StuID=stu).values_list('AveScore', flat=True))
                ascore_ = list(map(float, ascore_))
                ascoree_ = np.mean(ascore_)
                stuscorlist.append(ascoree_)
            # print(stuscorlist)
            numm = sum(ascoree >= j for j in stuscorlist)
            rat = numm / len(stuscorlist)
            if rat >= 0.8:
                str1 = "学霸"
        # print(str1)

        ##体质
        str2 = str3 = str4 = str5 = str6 = str7 = ""
        if Health.objects.filter(StuID=stuid):
            lis = list(Health.objects.filter(StuID=stuid))
            healthO = lis[-1]
            str2 = "身材" + healthO.HWLevel
            str3 = "体质" + healthO.TotalLevel
            if healthO.Meter50Level == "优秀":
                str4 = "短跑健将"
            if healthO.CrookLevel == "优秀":
                str5 = "柔韧性高"
            if healthO.JumpLevel == "优秀":
                str6 = "跳远健将"
            if healthO.Meter8001000Level == "优秀":
                str7 = "长跑健将"

        ##奖助学金
        str8 = ""
        if len(xx8) >= 2016 - int(Grade):
            str8 = "奖助学金达人"

        ##lib
        str9 = ""
        if ccc >= Tdelta / 2 and ccc > 5:
            str9 = "常驻图书馆"
        if ccc <= 5:
            str9 = "去图书馆次数少于5次"

        ##消费
        totlcos = round(-totlcos)
        # print(totlcos)
        str10 = ""
        if totlcos > 0:
            str10 = "最近一学期总消费约" + str(totlcos) + "元"

        cloud = [
            {"name": str0, "value": 2500},
            {"name": str11, "value": 2000},  # 成绩
            {"name": str1, "value": 2300},
            {"name": str2, "value": 2000},  # 身体
            {"name": str3, "value": 2000},
            {"name": str4, "value": 2000},
            {"name": str5, "value": 2000},
            {"name": str6, "value": 2000},
            {"name": str7, "value": 2000},
            {"name": str8, "value": 2300},  # 奖助学金
            {"name": str9, "value": 2000},  # lib
            {"name": str10, "value": 2000},  # 消费
            {"name": str12, "value": 2300},  # bas
            {"name": str13, "value": 2300},
            {"name": str14, "value": 2300},
            {"name": str15, "value": 2300},
            {"name": str16, "value": 2300},
            {"name": str17, "value": 2300},
            {"name": str18, "value": 2300}

        ]

        # print(cloud)

        # ret4charts = {'xx': xx, 'dd': dd,'xx2':xx2, 'dd2':dd2, 'xx3':xx3, 'dd3':dd3, 'cloud':cloud, 'dd5':dd5, 'dd6':dd6, 'dd7':dd7, 'xx8':xx8, 'dd8':dd8}

        retu = {'res1': res1, 'res2': res2, 'res3': res3, 'res4': res4, 'res9': res9, 'xx': xx, 'dd': dd, 'xx2': xx2,
                'dd2': dd2, 'xx3': xx3, 'dd3': dd3, 'cloud': cloud, 'dd5': dd5, 'dd6': dd6, 'dd7': dd7, 'xx8': xx8,
                'dd8': dd8}
        # print(retu)

        return HttpResponse(json.dumps(retu), content_type="application/json")


def queryY(request):
    if request.method == 'POST':
        # 关键内容
        stuid = request.POST.get('stuid')
        year = request.POST.get('year')
        # print(stuid)
        # 没有判空
        # objs = Lib.objects.filter(StuID=stuid, DateTime__year=year)
        # res5 = [obj.as_dict() for obj in objs]

        objs = HosReg.objects.filter(StuID=stuid, DateTime__year=year)
        res6 = [obj.as_dict() for obj in objs]

        objs = HosTrans.objects.filter(StuID=stuid, DateTime__year=year)
        res7 = [obj.as_dict() for obj in objs]

        objs = HosBX.objects.filter(StuID=stuid, DateTime__year=year)
        res8 = [obj.as_dict() for obj in objs]

        retu = {'res6': res6, 'res7': res7, 'res8': res8}
        # print(retu)

        return HttpResponse(json.dumps(retu), content_type="application/json")


dormlist = []
no1 = yes1 = 0


def monitor(request):
    # 读取学院信息，显示在下拉框上
    school_query_list = Basic.objects.values('School')
    school_list = list(set([tmp['School'] for tmp in school_query_list if tmp['School'] != '']))

    major_query_list = Basic.objects.filter(School=school_list[0]).values('Major')
    major_list = list(set([tmp['Major'] for tmp in major_query_list if tmp['Major'] != '']))

    grade_query_list = Basic.objects.filter(School=school_list[0], Major=major_list[0]).values('Grade')
    grade_list = list(set([tmp['Grade'] for tmp in grade_query_list if tmp['Grade'] != '']))

    class_query_list = Basic.objects.filter(School=school_list[0], Major=major_list[0], Grade=grade_list[0]).values(
        'classNo')
    class_list = list(set([tmp['classNo'] for tmp in class_query_list if tmp['classNo'] != '']))





    return render(request, 'servermaterial/monitor.html', context={'school_list': school_list,
                                                                   'major_list': major_list,
                                                                   'grade_list': grade_list,
                                                                   'class_list': class_list})



def monitor_engine(request):
    if request.method == 'POST':
        school = request.POST.get('school')
        major = request.POST.get('major')
        grade = request.POST.get('grade')
        clas = request.POST.get('class')



        pastTime = (datetime.datetime.now() - datetime.timedelta(days=730)).strftime('%Y-%m-%d %H:%M:%S')  # 过去3年时间
        print(pastTime)
        Tdelta = (datetime.datetime.strptime(pastTime, '%Y-%m-%d %H:%M:%S') - datetime.datetime.strptime('2017-02-20',
                                                                                                         '%Y-%m-%d')).days + 1  ###代替126

        ###查出所有学生 !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # stus = Basic.objects.filter(School=school, Major=major, Grade=grade, classNo=clas).values_list('StuID',
        #                                                                                                flat=True)

        stus = Basic.objects.filter(School=school).values_list('StuID',
                                                               flat=True)
        # print(stus)

        """
        生活规律
        """
        ###访问dorm
        global guilvlist  # 给list函数的
        dormlist = []
        for stuid in stus:
            dtlist = list(Dorm.objects.filter(StuID=stuid).values_list('DateTime', flat=True))
            if len(dtlist) != 0:
                nlist = np.zeros(Tdelta)
                for item in dtlist:
                    nitem = item.replace(tzinfo=None)
                    # nitem = datetime.datetime.strptime(item, '%Y-%m-%d %H:%M:%S.000000')
                    if datetime.datetime.strptime('2017-02-20 00:00:00',
                                                  '%Y-%m-%d %H:%M:%S') <= nitem <= datetime.datetime.strptime(pastTime,
                                                                                                              '%Y-%m-%d %H:%M:%S'):
                        delta = (nitem - datetime.datetime.strptime('2017-02-20', '%Y-%m-%d')).days
                        nlist[delta] += 1
                # print(nlist)
                nlist = list(nlist)
                dormc = Tdelta - nlist.count(0)
                freq4dorm = dormc / float(Tdelta)  ###回寝室不规律
                if freq4dorm < 0.7:
                    dormlist.append(stuid)
        # rat = len(dormlist)/float(len(stus))
        # print('比例1')
        # print(rat)
        # print(dormlist)

        ###食堂等
        consulist = []
        for stuid in stus:
            dtlist = list(Card.objects.filter(StuID=stuid).values_list('DateTime', flat=True))
            costlist = list(Card.objects.filter(StuID=stuid).values_list('Cost', flat=True))
            if len(dtlist) != 0:
                nlist = np.zeros(Tdelta)
                for item in range(len(dtlist)):
                    nitem = datetime.datetime.strptime(dtlist[item], '%Y-%m-%d %H:%M:%S').replace(tzinfo=None)
                    if datetime.datetime.strptime('2017-02-20 00:00:00',
                                                  '%Y-%m-%d %H:%M:%S') <= nitem <= datetime.datetime.strptime(pastTime,
                                                                                                              '%Y-%m-%d %H:%M:%S'):
                        delta = (nitem - datetime.datetime.strptime('2017-02-20', '%Y-%m-%d')).days
                        if float(costlist[item]) < 0:
                            nlist[delta] += float(costlist[item])
                # print(nlist)
                nlist = list(nlist)
                consuc = Tdelta - nlist.count(0)
                freq4consu = consuc / float(Tdelta)  ###吃饭不规律
                if freq4consu < 0.7:
                    consulist.append(stuid)
        # rat = len(consulist) / float(len(stus))
        # print('比例2')
        # print(rat)
        # print(consulist)

        ###合并
        dormlist.extend(consulist)
        guilvlist = list(set(dormlist))
        # rat = len(dormlist)/float(len(stus))

        # print('比例')
        # print(rat)
        # print(dormlist)
        global no1
        no1 = len(guilvlist)
        no1d = {'value': no1, 'name': '不规律'}
        global yes1
        yes1 = len(stus) - no1
        yes1d = {'value': yes1, 'name': '规律'}
        cha1 = [no1d, yes1d]

        """
        不及格监测
        """
        global bujigejiancelist  # 给list函数的
        global kemushu
        bujigejiancelist = []
        kemushu = []
        for stuid in stus:
            dtlist1 = list(Score.objects.filter(StuID=stuid).values_list('Low60', flat=True))
            cccc = 0
            for it in dtlist1:
                cccc += int(it)
            dtlist2 = list(Score.objects.filter(StuID=stuid).values_list('Num0', flat=True))
            for it in dtlist2:
                cccc += int(it)

            if cccc != 0:
                bujigejiancelist.append(stuid)
                kemushu.append(cccc)

        global no2
        no2 = len(bujigejiancelist)
        no2d = {'value': no2, 'name': '不及格'}
        global yes2
        yes2 = len(stus) - no2
        yes2d = {'value': yes2, 'name': '及格'}
        cha2 = [no2d, yes2d]

        """
        不及格预警
        """
        tst()
        global bujigeyujinglist  # 给list函数的
        bujigeyujinglist = []
        for stuid in stus:
            dtlist = list(PredScore.objects.filter(StuID=stuid).values_list('Score', flat=True))
            if len(dtlist) != 0 and float(dtlist[0]) < 70:
                bujigeyujinglist.append(stuid)

        global no3
        no3 = len(bujigeyujinglist)
        no3d = {'value': no3, 'name': '不及格'}
        global yes3
        yes3 = len(stus) - no3
        yes3d = {'value': yes3, 'name': '及格'}
        cha3 = [no3d, yes3d]

        """
        身体健康监测
        """
        global jiankangjiancelist  # 给list函数的
        jiankangjiancelist = []
        for stuid in stus:
            dtlist = list(Health.objects.filter(StuID=stuid).values_list('TotalLevel', flat=True))
            if len(dtlist) != 0 and dtlist[-1] == "不及格":
                jiankangjiancelist.append(stuid)

        for stuid in stus:
            dtlist = list(HosReg.objects.filter(StuID=stuid).values_list('DateTime', flat=True))
            if len(dtlist) != 0:
                nlist = np.zeros(Tdelta)
                for item in dtlist:
                    nitem = item.replace(tzinfo=None)
                    # nitem = datetime.datetime.strptime(item, '%Y-%m-%d %H:%M:%S.000000')
                    if datetime.datetime.strptime('2017-02-20 00:00:00',
                                                  '%Y-%m-%d %H:%M:%S') <= nitem <= datetime.datetime.strptime(pastTime,
                                                                                                              '%Y-%m-%d %H:%M:%S'):
                        delta = (nitem - datetime.datetime.strptime('2017-02-20', '%Y-%m-%d')).days
                        nlist[delta] += 1
                # print(nlist)
                nlist = list(nlist)
                hosc = Tdelta - nlist.count(0)
                freq4hos = hosc / float(Tdelta)  ###去医院就诊太勤
                if freq4hos > 0.3:
                    jiankangjiancelist.append(stuid)

        jiankangjiancelist = list(set(jiankangjiancelist))

        global no4
        no4 = len(jiankangjiancelist)
        no4d = {'value': no4, 'name': '不健康'}
        global yes4
        yes4 = len(stus) - no4
        yes4d = {'value': yes4, 'name': '健康'}
        cha4 = [no4d, yes4d]

        """
        退学预警
        """
        global tuixuelist  # 给list函数的
        tuixuelist = []
        #tst()

        for stuid in stus:
            dtlist = list(Score.objects.filter(StuID=stuid).values_list('AveScore', flat=True))
            dtlist = list(map(float, dtlist))
            if len(list(PredScore.objects.filter(StuID=stuid).values_list('Score', flat=True))) != 0:
                nsum = 0  # 为了求均值
                for i in range(len(dtlist)):
                    nsum += dtlist[i]

                preval = list(PredScore.objects.filter(StuID=stuid).values_list('Score', flat=True))[0]
                nsum += float(preval)
                aaas = nsum / (len(dtlist) + 1)
                # print(aaas)
                if aaas < 70:
                    tuixuelist.append(stuid)

        global no5
        no5 = len(tuixuelist)
        no5d = {'value': no5, 'name': '有退学风险'}
        global yes5
        yes5 = len(stus) - no5
        yes5d = {'value': yes5, 'name': '无退学风险'}
        cha5 = [no5d, yes5d]

        retu = {'cha1': cha1, 'cha2': cha2, 'cha3': cha3, 'cha4': cha4, 'cha5': cha5}

        print(retu)

        return HttpResponse(json.dumps(retu), content_type="application/json")





def list1(request):
    global bujigejiancelist
    global kemushu
    global no2
    global yes2
    no2d = {'value': no2, 'name': '不及格'}
    yes2d = {'value': yes2, 'name': '及格'}
    cha1 = [no2d, yes2d]
    retu = {'cha1': cha1}

    ###表格
    res4 = []
    for stuid in bujigejiancelist:
        objs4 = Basic.objects.filter(StuID=stuid)[0]
        data = {
            'StuID': objs4.StuID,
            'School': objs4.School,
            'Major': objs4.Major,
            'classNo': objs4.classNo
        }
        res4.append(data)

    if len(bujigejiancelist) != 0:
        for ii in range(len(bujigejiancelist)):
            res4[ii].update({'bujici': kemushu[ii]})
    print(res4)



    return render(request, 'servermaterial/list1.html', {'retu': json.dumps(retu), 'res4': json.dumps(res4)})


def list2(request):
    global bujigeyujinglist
    global no3
    global yes3
    no3d = {'value': no3, 'name': '不及格'}
    yes3d = {'value': yes3, 'name': '及格'}
    cha1 = [no3d, yes3d]
    retu = {'cha1': cha1}

    ###表格
    res4 = []
    for stuid in bujigeyujinglist:
        objs4 = Basic.objects.filter(StuID=stuid)[0]
        data = {
            'StuID': objs4.StuID,
            'School': objs4.School,
            'Major': objs4.Major,
            'classNo': objs4.classNo
        }
        res4.append(data)
    print(res4)

    return render(request, 'servermaterial/list2.html', {'retu': json.dumps(retu), 'res4': json.dumps(res4)})


def list3(request):
    global tuixuelist
    global no5
    global yes5
    no5d = {'value': no5, 'name': '有退学风险'}
    yes5d = {'value': yes5, 'name': '无退学风险'}
    cha1 = [no5d, yes5d]
    retu = {'cha1': cha1}

    ###表格
    res4 = []
    for stuid in tuixuelist:
        objs4 = Basic.objects.filter(StuID=stuid)[0]
        data = {
            'StuID': objs4.StuID,
            'School': objs4.School,
            'Major': objs4.Major,
            'classNo': objs4.classNo
        }
        res4.append(data)
    print(res4)

    return render(request, 'servermaterial/list3.html', {'retu': json.dumps(retu), 'res4': json.dumps(res4)})


def list4(request):
    global guilvlist
    global no1
    global yes1
    no1d = {'value': no1, 'name': '不规律'}
    yes1d = {'value': yes1, 'name': '规律'}
    cha1 = [no1d, yes1d]
    retu = {'cha1': cha1}

    ###表格
    res4 = []
    for stuid in guilvlist:
        objs4 = Basic.objects.filter(StuID=stuid)[0]
        data = {
            'StuID': objs4.StuID,
            'School': objs4.School,
            'Major': objs4.Major,
            'classNo': objs4.classNo
        }
        res4.append(data)
    print(res4)

    return render(request, 'servermaterial/list4.html', {'retu': json.dumps(retu), 'res4': json.dumps(res4)})


def list5(request):
    global jiankangjiancelist
    global no4
    global yes4
    no4d = {'value': no4, 'name': '不健康'}
    yes4d = {'value': yes4, 'name': '健康'}
    cha1 = [no4d, yes4d]
    retu = {'cha1': cha1}

    ###表格
    res4 = []
    for stuid in jiankangjiancelist:
        objs4 = Basic.objects.filter(StuID=stuid)
        res4 = [obj.as_dict() for obj in objs4]
    print(res4)

    return render(request, 'servermaterial/list5.html', {'retu': json.dumps(retu), 'res4': json.dumps(res4)})


def data_import_export(request):
    return render(request, 'servermaterial/data_import_export.html')


def intervene(request):
    """
    干预页面
    :param request:
    :return:
    """
    # 读取学院信息，显示在下拉框上
    school_query_list = Basic.objects.values('School')
    school_list = list(set([tmp['School'] for tmp in school_query_list if tmp['School'] != '']))
    major_query_list = Basic.objects.filter(School=school_list[0]).values('Major')
    major_list = list(set([tmp['Major'] for tmp in major_query_list if tmp['Major'] != '']))
    class_list = []
    if major_list.__len__() != 0:
        class_query_list = Basic.objects.filter(School=school_list[0], Major=major_list[0].strip(),
                                                Entrance__startswith='2013').values("classNo")
        class_list = list(set(tmp['classNo'] for tmp in class_query_list))
    return render(request, 'servermaterial/intervene.html', context={'school_list': school_list,
                                                                     'major_list': major_list,
                                                                     'class_list': class_list})


def CheckData(request):
    if request.method == "POST":
        f = request.FILES['inputFile']
        db_type = request.POST['db_type']
        file_type = f.name.split('.')[1]
        return_data = []
        message = '文件解析成功！'
        if file_type == 'xlsx':
            wb = xlrd.open_workbook(filename=None, file_contents=f.read())  # 关键点在于这里
            table = wb.sheets()[0]
            nrows = table.nrows
            try:
                with transaction.atomic():
                    if db_type == '图书馆借阅记录':
                        for i in range(1, nrows):
                            rowValues = table.row_values(i)
                            models.Book.objects.get_or_create(StuID=rowValues[0], BookID=rowValues[1],
                                                              Date=rowValues[2], OperType=rowValues[3],
                                                              StuType=rowValues[4], Department=rowValues[5])
                            return_data.append(rowValues)
            except Exception as e:
                message = '文件读取出现错误'
        else:
            for line in f:
                info_list = line.decode().split(',')
                print(info_list)
                Lib.objects.get_or_create(StuID=info_list[1], Gate=info_list[2], DateTime=info_list[3])
        # ret = {'message': message, 'data': return_data, 'data_type': db_type}
        # return HttpResponse(json.dumps(ret), content_type='application/json')
        return render(request, "servermaterial/data_import_export.html", context={'message': '上传成功'})


def download(request):
    if request.method == 'POST':
        db_type = request.POST['db_type']
        if db_type == '图书馆借阅记录':
            contents = models.Book.objects.all()
            response = HttpResponse(content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename=export_data.xls'  # 返回下载文件的名称(activity.xls)
            workbook = xlwt.Workbook(encoding='utf-8')  # 创建工作簿
            mysheet = workbook.add_sheet(u'图书馆借阅记录')  # 创建工作页
            rows = contents
            cols = 6  # 每行的列
            aaa = ['学号', '图书编号', '时间', '操作类型', '学生类型', '部门']  # 表头名
            for c in range(len(aaa)):
                mysheet.write(0, c, aaa[c])
            for r in range(0, len(rows)):  # 对行进行遍历
                mysheet.write(r + 1, 0, str(rows[r].StuID))
                mysheet.write(r + 1, 1, str(rows[r].BookID))
                mysheet.write(r + 1, 2, str(rows[r].Date))
                mysheet.write(r + 1, 3, str(rows[r].OperType))
                mysheet.write(r + 1, 4, str(rows[r].StuType))
                mysheet.write(r + 1, 5, str(rows[r].Department))
            response = HttpResponse(
                content_type='application/vnd.ms-excel')  # 这里响应对象获得了一个特殊的mime类型,告诉浏览器这是个excel文件不是html
            response[
                'Content-Disposition'] = 'attachment; filename=export_data.xls'  # 这里响应对象获得了附加的Content-Disposition协议头,它含有excel文件的名称,文件名随意,当浏览器访问它时,会以"另存为"对话框中使用它.
            workbook.save(response)
            return response


def View(request):
    db_type = request.POST['db']
    if db_type == "图书馆借阅记录":
        contents = Lib.objects.all()
        lines = [c.as_dict() for c in contents]
        # ret = {'lines': lines}
        return HttpResponse(json.dumps(lines), content_type='application/json')


def query_majors(request):
    """
    查询 指定学校的所有专业
    :param request:
    :return: 专业list(json数据格式)
    """
    data = json.loads(request.body.decode())
    print(data)
    major_query_list = Basic.objects.filter(School=data['school'].strip()).values('Major')

    major_set = set([tmp['Major'] for tmp in major_query_list if tmp['Major'] != ''])
    return HttpResponse(json.dumps(list(major_set)), content_type='application/json')


def query_grades(request):
    """
     给定 学院+专业 查年级list询所有年级信息
     :param request: (json数据格式)
     :return:
     """
    data = json.loads(request.body.decode())  # 浏览器端用ajax传来json字典数据
    grade_query_list = Basic.objects.filter(School=data['school'].strip(), Major=data['major'].strip()).values("Grade")
    grade_list = list(set(tmp['Grade'] for tmp in grade_query_list))
    if grade_list.__len__() == 0:
        grade_list.append('NULL')
    print(grade_list)
    return HttpResponse(json.dumps(grade_list), content_type='application/json')


def query_class(request):
    """
    给定 学院+专业+年级 查询所有班级信息
    :param request: 班级list(json数据格式)
    :return:
    """
    data = json.loads(request.body.decode())  # 浏览器端用ajax传来json字典数据
    if data['grade'].strip() == 'NULL':
        class_list = ['NULL']
    else:
        # print(data)
        class_query_list = Basic.objects.filter(School=data['school'].strip(), Major=data['major'].strip(),
                                                Grade=data['grade'].strip()).values("classNo")
        class_list = list(set(tmp['classNo'] for tmp in class_query_list))
        if class_list.__len__() == 0:
            class_list.append('NULL')
        print(class_list)
    return HttpResponse(json.dumps(class_list), content_type='application/json')


def query_ID(request):
    """
    给定 学院+专业+年级+班级 查询所有ID信息
    :param request: IDlist(json数据格式)
    :return:
    """
    data = json.loads(request.body.decode())  # 浏览器端用ajax传来json字典数据
    if data['grade'].strip() == 'NULL' or data['class'].strip() == 'NULL':
        id_list = ['NULL']
    else:
        id_query_list = Basic.objects.filter(School=data['school'].strip(), Major=data['major'].strip(),
                                             Grade=data['grade'].strip(), classNo=data['class'].strip()).values("StuID")
        print(id_query_list)
        id_list = list(set(tmp['StuID'] for tmp in id_query_list))
        if id_list.__len__() == 0:
            id_list.append('NULL')
        print(id_list)
    return HttpResponse(json.dumps(id_list), content_type='application/json')


def query_intervene(request):
    """
    查询干预意见接口
    :param request:
    :return: 干预意见(json数据格式)
    """
    data = json.loads(request.body.decode())
    objs = InterveneSuggestion.objects
    # 查询单个学生
    if len(data) == 1:
        stu_id = data['stuNo']  # 查询不到该学生
        if len(Basic.objects.filter(StuID=stu_id)) == 0:
            return JsonResponse({"info": '查无此人'})
        school = Basic.objects.filter(StuID=stu_id)[0].School
        # ------------------------------------------假设暂时有这三个标签，后续应从接口中获取--------------------------------------
        labels = {'study_state': '学霸', 'is_fail_exam': False, 'body_health_state': '较差'}
        # -----------------------------------------------------------------------------------------------------------------
        intervene_suggestion = objs.filter(study_state=labels['study_state'],
                                           is_fail_exam=labels['is_fail_exam'],
                                           body_health_state=labels['body_health_state'])
        dict_intervene = intervene_suggestion[0].as_dict()
        dict_intervene['school'] = school
        dict_intervene['stu_id'] = stu_id
        return JsonResponse(data=dict_intervene)
    # 查询班级学生
    else:
        stu_query_set = Basic.objects.filter(School=data['school'].strip(), Major=data['major'].strip(),
                                             Entrance__startswith=data['grade'].strip())
        if data['classNo'] != '所有班级':
            stu_query_set = stu_query_set.filter(classNo=data['classNo'])
        stu_id_list = [tmp['StuID'] for tmp in stu_query_set.values('StuID')]
        list_intervene = []
        for id in stu_id_list:
            # ------------------------------------------假设暂时有这三个标签，后续应从接口中获取--------------------------------------
            labels = {'study_state': '学霸', 'is_fail_exam': False, 'body_health_state': '较差'}
            # -----------------------------------------------------------------------------------------------------------------
            intervene_suggestion = objs.filter(study_state=labels['study_state'],
                                               is_fail_exam=labels['is_fail_exam'],
                                               body_health_state=labels['body_health_state'])
            single_intervene = intervene_suggestion[0].as_dict()
            single_intervene['school'], single_intervene['stu_id'] = data['school'], id
            list_intervene.append(single_intervene)
        return HttpResponse(json.dumps(list_intervene), content_type="application/json")


def get_hot_book_list(request):
    """
    热门书籍列表
    :param request:
    :return:每一本书用一个字典对象(有name属性，values属性，itemStyle属性)
    """
    topk = 10
    school_name = "全校学生"
    if request.method == "POST":
        topk = int(request.POST['k'])
        school_name = request.POST['schoolName'].strip()
        print(school_name)
    topk_name_list = []
    print(topk)
    topk_name_list, topk_count_list = get_hot_book(topk, school_name)
    data = []
    for i in range(len(topk_name_list)):
        book = {'name': topk_name_list[i], 'value': topk_count_list[i]}
        data.append(book)
    return JsonResponse(data=data, safe=False)


def recommend(request):
    """
    推荐页面
    :param request:
    :return:
    """
    if request.method == "POST":
        idr = int(stu_inverse_dict[request.POST['idr']])
        get_recommend_list(idr)
        book_id_list = get_recommend_list(idr)
        book_loc_list = [book_dict[str(v)].strip() for v in book_id_list]
        print(book_loc_list)
        book_name_list = []
        with connection.cursor() as cursor:
            for loc in book_loc_list:
                cursor.execute('select book_name from book_info where location=' + '\'' + loc + '\'')
                row = cursor.fetchone()
                book_name_list.append(row[0])
        stu_id = stu_dict[str(idr)]
        return JsonResponse(data=book_name_list, safe=False)
    recommend_dict = {}
    school_query_list = Basic.objects.values('School')
    school_list = list(set([tmp['School'] for tmp in school_query_list if tmp['School'] != '']))
    print(school_list)
    major_query_list = Basic.objects.filter(School=school_list[0]).values('Major')
    major_list = list(set([tmp['Major'] for tmp in major_query_list if tmp['Major'] != '']))
    return render(request, 'servermaterial/recommend.html', context={'recommend_dict': recommend_dict,
                                                                     'school_list': school_list,
                                                                     'major_list': major_list, })


def tt(request):
    with connection.cursor() as cursor:
        cursor.execute('select * from web_basic')
        row = cursor.fetchone()
        print(row[1])
    return HttpResponse(row)


def index(request):
    """
    index页面
    :param request:
    :return:
    """
    return render(request, "servermaterial/index_main.html")


def tst():
    np.random.seed(1119)

    stuolist = Score.objects.all()
    stulist = []
    for i in stuolist:
        if i.StuID not in stulist:
            stulist.append(i.StuID)
    # print(stulist)

    # x_test = np.array( pd.read_csv("x_test.csv",header=None) )
    # x_test = np.reshape(x_test,(x_test.shape[0],7,1))
    """
    上面是文件格式
    下面是一个个学生，list格式
    """
    # x_test = np.array([78.86,74.89,-2,-2,-2,-2,-2])
    # x_test = np.reshape(x_test,(1,7,1))

    scorlists = []
    for u in stulist:
        scorlist = list(Score.objects.filter(StuID=u).values_list('AveScore', flat=True))
        scorlist = list(map(float, scorlist))
        num = 7 - scorlist.__len__()
        for i in range(num):
            scorlist.append(-2)

        scorlists.append(scorlist)

    x_test = np.array(scorlists)
    #print(x_test)
    x_test = np.reshape(x_test, (x_test.shape[0], 7, 1))

    batch_size = 32  # 超参
    epochs = 1000  # 超参
    units = 6  # 超参 4不行

    keras.backend.clear_session()
    model = Sequential()
    model.add(Masking(mask_value=-2., input_shape=(7, 1)))
    model.add(LSTM(units))
    model.add(Dense(1))
    #print(model.summary())
    model.compile(loss='mean_squared_error', optimizer='adam', metrics=['mse', 'mape'])

    # filepath = './lstmfc/model-ep{epoch:03d}-mse{mean_squared_error:.3f}-val_mse{val_mean_squared_error:.3f}-val_mape{val_mean_absolute_percentage_error}.h5'
    # checkpoint = keras.callbacks.ModelCheckpoint(filepath, monitor='val_mean_squared_error', verbose=1, save_best_only=True, mode='min')
    # model.fit(x_train, y_train, epochs=epochs, batch_size=batch_size, verbose=1, validation_data=(x_test, y_test), shuffle=True, callbacks=[checkpoint])

    ###predict
    # model.load_weights('C:\\Users\\ICE\\education-system\\WebTool\\web\\lstmfc\\model-ep995-mse28.667-val_mse28.815-val_mape4.917600361394993.h5')
    model.load_weights('./web/lstmfc/model-ep995-mse28.667-val_mse28.815-val_mape4.917600361394993.h5')
    print('load weights...')
    reeee = model.predict(x_test)
    reeee = np.reshape(reeee, (len(stulist),))
    #print(reeee)
    print(reeee.shape)  # （200,1）-->(200,)

    PredScore.objects.all().delete()
    # print('deeeeeeeeeeeeeeeeel')
    addlist = []
    for i in range(len(stulist)):
        obj = PredScore(
            StuID=stulist[i],
            Score=reeee[i]
        )
        addlist.append(obj)
    PredScore.objects.bulk_create(addlist)
    # print('inssssssssssssssssssssss')
