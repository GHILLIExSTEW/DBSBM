-- Sync cappers table with win/loss/push counts from unit_records
-- This script updates the bet_won, bet_loss, bet_push fields in cappers table
-- based on the actual bet results from unit_records

UPDATE cappers c
SET
    bet_won = (
        SELECT COUNT(*)
        FROM unit_records ur
        JOIN bets b ON ur.bet_serial = b.bet_serial
        WHERE b.user_id = c.user_id
        AND b.guild_id = c.guild_id
        AND b.status = 'won'
    ),
    bet_loss = (
        SELECT COUNT(*)
        FROM unit_records ur
        JOIN bets b ON ur.bet_serial = b.bet_serial
        WHERE b.user_id = c.user_id
        AND b.guild_id = c.guild_id
        AND b.status = 'lost'
    ),
    bet_push = (
        SELECT COUNT(*)
        FROM unit_records ur
        JOIN bets b ON ur.bet_serial = b.bet_serial
        WHERE b.user_id = c.user_id
        AND b.guild_id = c.guild_id
        AND b.status = 'push'
    ),
    updated_at = UTC_TIMESTAMP()
WHERE EXISTS (
    SELECT 1
    FROM unit_records ur
    JOIN bets b ON ur.bet_serial = b.bet_serial
    WHERE b.user_id = c.user_id
    AND b.guild_id = c.guild_id
);
