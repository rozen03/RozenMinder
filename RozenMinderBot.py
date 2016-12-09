#!/usr/bin/python3
# -*- coding: utf-8 -*-
import logging
import telegram
from telegram.error import NetworkError, Unauthorized
from time import sleep
from telegram.ext import Job
from commontools import *
from tookns import RozenMindertookn

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


#def createReminder(bot,update,groups):

def makeARemind(bot,job):
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
	inFiveMinutes= ahoraMasMinutos(+5)
	with db_session:
		nextReminds = select(r for r in Remind if now<=r.last+r.repeat and r.last+r.repeat<inFiveMinutes)[:]
		for remind in nextReminds:
			remind_job = Job(makeARemind, interval=0, repeat=False, context=remind.id)
			job.job_queue.put(remind_job,next_t=(remind.last+remind.repeat - ahoraMasHoras(0)).total_seconds())
	mandarARozen(bot, str(job.job_queue))

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
		handler = MessageHandler(Filters.text | Filters.command, registrar)
		dispatcher.add_handler(handler)
		dispatcher.add_handler(CallbackQueryHandler(button))
		dispatcher.add_handler(
			MessageHandler(
				Filters.status_update,
				registrarIO))
		job_minute = Job(callback_minute, 300.0)
		j.put(job_minute, next_t=0.0)
		#with db_session:
		#	trash = Remind(user=User.get(id_user=137497264),start=ahoraMasMinutos(1),last=ahoraMasMinutos(1),text="Funca :D")
		#updater.start_polling()

    	# Add conversation handler with the states GENDER, PHOTO, LOCATION and BIO
#    	conv_handler = ConversationHandler(
#        	entry_points=[CommandHandler('start', start)],
#        	states={
#            	CHOOSING_TIME: [RegexHandler('^(Age|Favourite colour|Number of siblings)$',
#                                    	regular_choice,
#                                    	pass_user_data=True),
#                       					RegexHandler('^Something else...$',
#                                    	custom_choice),
#                ],
#				CONFIRMING_TIME: [MessageHandler(Filters.text,
#                                           regular_choice,
#                                           pass_user_data=True),
#                ],
#
#				TYPING_CHOICE: [MessageHandler(Filters.text,
#                                           regular_choice,
#                                           pass_user_data=True),
#                ],
#            	TYPING_REPLY: [MessageHandler(Filters.text,
#                                          received_information,
#                                          pass_user_data=True),
#                ],
#        	},
#        	fallbacks=[RegexHandler('^Done$', done, pass_user_data=True)]
#    	)
#    	dispatcher.add_handler(conv_handler)

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
