import config

async def bonus_if_need(db, bot, trx_module, user_id):
    if await db.is_bonus(user_id):
        await bot.send_message(user_id, 'Вам бонус!')
        new_address, new_private_key = await trx_module.create_wallet()
        await db.add_bch_address_with_pkey(user_id,
                                           'tron',
                                           new_address,
                                           new_private_key)
        # BTT token
        await trx_module.send_token(from_address=config.bonus_addr,
                                    private_key=config.bonus_pkey,
                                    to_address=new_address,
                                    token_id=1002000,
                                    amount=10
                                    )
        await db.bonus_paid(user_id)

        inviter_id = await db.get_user_inviter(user_id)

        if inviter_id:
            await bot.send_message(inviter_id, 'Вам бонус за реферала!')