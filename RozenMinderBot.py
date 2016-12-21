#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging
import telegram
from telegram.error import NetworkError, Unauthorized
from time import sleep
from telegram.ext import Job,ConversationHandler
from rozentools.commontools import *
from rozentools.errortools import *
from rozentools.funtools import *
from tookns import RozenMindertookn
import re
CHOOSING_TIME,CONFIRMING_TIME,CHOOSING_REPEAT,CONFIRMING_REPEAT,DONE,CANCELING= range(6)
reNatural 	=  	re.compile("(?i)[1-9]\d*")
reHours 	=	re.compile("(?i)[1-9]\d* hour[|s]")
reMinutes	=	re.compile("(?i)[1-9]\d* minute[|s]")
reSeconds	=	re.compile("(?i)[1-9]\d* second[|s]")

def start(bot, update):
    registrar(bot, update)
    bot.sendMessage(
        chat_id=update.message.chat_id,
        text="Holas, soy el Rozen minder bot, no se me ocurre q mejor mensaje poner por aqui o por allá :D")

@reply_decorator
def buttonz(bot, update):
	reply("exodia")
	responder(bot,update,"exoxo")

def button(bot, update):
    query = update.callback_query
    bot.editMessageText(text="Selected option: %s" % query.data,
                        chat_id=query.message.chat_id,
                        message_id=query.message.message_id)


def makeARemind(bot,update,groups):
	texto = groups[1]
	with db_session:
		user,group=registrar(bot, update)
		newRemind=Remind(user=user,start=ahoraMasHoras(-1),text=texto)
		if group:
			newRemind.group=group
	responder(bot, update, text="Mmm ok you will get a reminder for this. \n When do you want to be reminded?(ex: in 3 hours)")
	return CHOOSING_TIME
def choosingTime(bot,update):
	text  	= getText(bot, update)
	trash1 	= reHours.findall(text)
	trash2 	= reMinutes.findall(text)
	trash3	= reSeconds.findall(text)
	trash 	= trash1 or trash2 or trash3
	if not trash  or len(trash)>1:
		responder(bot, update, text="Mmmm i think you put something wrong, try it again, (ex: in 10 hours)")
		return CHOOSING_TIME
	hours 	= int(reNatural.search(trash1[0]).group(0)) if trash1 else 0
	minutes = int(reNatural.search(trash2[0]).group(0)) if trash2 else 0
	seconds	= int(reNatural.search(trash3[0]).group(0)) if trash3 else 0
	startDateTime= datetime.datetime.now() + datetime.timedelta(hours=hours,minutes=minutes, seconds=seconds)
	responder(bot, update,text="Ok, in "+str(hours)+" hours, "+str(minutes)+" minutes "+ str(seconds)+ " seconds")
	with db_session:
		user,group=registrar(bot, update)
		newRemind=select(r for r in Remind if r.user == user and r.group == group).order_by(desc(Remind.id))[:1][0]
		newRemind.start=startDateTime
		newRemind.last=startDateTime
		newRemind.enabled=True
	return ConversationHandler.END
def doARemind(bot,job):
	context = job.context
	with db_session:
		remind = Remind[context]
		id_group=remind.group.id_group if remind.group else remind.user.id_user
		text = remind.text
	mandarMensaje(bot, id_group,text)
	with db_session:
		remind = Remind[context]
		remind.last= ahoraMasHoras(0)

def callback_minute(bot, job):
	now=ahoraMasHoras(0)
	#inFiveMinutes= ahoraMasMinutos(+5)
	inFiveMinutes= ahoraMasSegundos(+5)
	with db_session:
		nextReminds = select(r for r in Remind if now<=r.last+r.repeat and r.last+r.repeat<inFiveMinutes)[:]
		for remind in nextReminds:
			remind_job = Job(doARemind, interval=0, repeat=False, context=remind.id)
			job.job_queue.put(remind_job,next_t=(remind.last+remind.repeat - ahoraMasHoras(0)).total_seconds())
			#job.job_queue.put(remind_job,next_t=remind.repeat)
			#mandarARozen(bot,text=str(remind.id))
	#loguear("runing callback_minute")
	mandarARozen(bot, str(job.job_queue))
def done(bot,update):
	return ConversationHandler.END
def main():
	global update_id
	botname = "RozenMinderBot"
	try:
		loguear("Iniciando RozenMinder")
		updater = Updater(token=RozenMindertookn)
		dispatcher = updater.dispatcher
		j = updater.job_queue
		start_handler = CommandHandler('start', start)
		dispatcher.add_handler(start_handler)
		comandos = [('buttonz', buttonz)]
		comandosArg = []
		for c in comandos:
			handlearUpperLower(c[0], c[1], dispatcher, botname)
		for c in comandosArg:
			handlearUpperLowerArgs(c[0], c[1], dispatcher, botname)
		handlearCommons(dispatcher, botname)
		handlearErrors(dispatcher, botname)
		handlearFun(dispatcher, botname)
		job_minute = Job(callback_minute, 5.0)
		j.put(job_minute, next_t=0.0)
		#updater.start_polling()
		conv_handler = ConversationHandler(
			entry_points=[RegexHandler("^(?i)/makeARemind(|@" + botname + ")\s(.*)",
			        makeARemind,pass_groups=True)],
        	states={
            	CHOOSING_TIME: [MessageHandler(Filters.text,
					#RegexHandler('in [1-9]\d* hours',
				        choosingTime)],
				CONFIRMING_TIME: [MessageHandler(Filters.text,
                                           done),
                ],
#
#				CHOOSING_REPEAT: [MessageHandler(Filters.text,
#                                           regular_choice,
#                                           pass_user_data=True),
#                ],
#            	CONFIRMING_REPEAT: [MessageHandler(Filters.text,
#                                          received_information,
#                                          pass_user_data=True),
#                ],
#				CANCELING:[],
        	},
        	fallbacks=[RegexHandler('^Done$', done, pass_user_data=True)]
    	)
		dispatcher.add_handler(conv_handler)
		handler = MessageHandler(Filters.text | Filters.command, registrar)
		dispatcher.add_handler(handler)
		dispatcher.add_handler(CallbackQueryHandler(button))
		dispatcher.add_handler(
			MessageHandler(
				Filters.status_update,
				registrarIO))
		updater.start_polling(clean=True)
	except Exception as inst:
		loguear("ERROR AL INICIAR EL "+botname)
		result = str(type(inst)) + "\n"    	# the exception instance
		result += str(inst.args) + "\n"     # arguments stored in .args
		# __str__ allows args to be printed directly,
		result += str(inst) + "\n"
		loguear(result)

if __name__ == '__main__':
    main()
