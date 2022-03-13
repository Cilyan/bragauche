import click


@click.command()
@click.option(
    '--joydbg',
    is_flag=True,
    help='Special program for joystick debugging',
)
@click.argument('port')
def bragauche(joydbg, port):
    if joydbg:
        from .debug import joystick_debug
        joystick_debug()
    else:
        from .controller import control
        control(port)
