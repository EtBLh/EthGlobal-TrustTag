
import ExchangeIcon from '@/icons/exchange.svg?react'
import UserIcon from '@/icons/user.svg?react'
import GambleIcon from '@/icons/gamble.svg?react'
import DangerIcon from '@/icons/danger.svg?react'
import CustomizeIcon from '@/icons/setting.svg?react'
import { cn } from "@/lib/utils"
import { proposal } from '@/lib/type'

const colors = {
    normal: ['#250C61', '#7548D7'],
    good: ['#064428', '#53D299'],
    warning: ['#443E04', '#D5C455'],
    danger: ['#440D06','#D65C4C']
}

const tagTypeColor = {
    normal_user: colors.good,
    exchange: colors.normal,
    gamble: colors.warning,
    scam: colors.danger
}

export const ProposalIcon = (props: {type: string, className?: string}) => {
    const {type} = props;
    let color = ["#202020", "#eee"] //default color
    if (type in tagTypeColor) {
       color = tagTypeColor[type as proposal['tag']];
    }
    const iconStyle = {
        style:{width: 24, height: 24},
        color: color[1]
    }
    return (
        <div className={cn("rounded-full w-[40px] h-[40px] flex items-center justify-center", props.className)} style={{background: color[0]}}>
            {
                type === 'exchange' && <ExchangeIcon {...iconStyle}/>
            }
            {
                type === 'normal_user' && <UserIcon {...iconStyle}/>
            }
            {
                type === 'gamble' && <GambleIcon {...iconStyle}/>
            }
            {
                type === 'scam' && <DangerIcon {...iconStyle}/>
            }
            {
                type !== 'exchange' && type !== 'normal_user' && type !== 'gamble' && type !== 'scam' &&
                    <CustomizeIcon {...iconStyle}/>
            }
        </div>
    )
}
