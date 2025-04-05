import { proposal } from "@/type"
import ExchangeIcon from '@/icons/exchange.svg?react'
import UserIcon from '@/icons/user.svg?react'
import GambleIcon from '@/icons/gamble.svg?react'
import DangerIcon from '@/icons/danger.svg?react'
import { shortenAddr } from "@/util"
import { cn } from "@/lib/utils"
import { Button } from "./ui/button"
import { Link } from "react-router"

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

const ProposalIcon = (props: {type: proposal['tag']}) => {
    const {type} = props;
    return (
        <div className={cn("rounded-full w-[40px] h-[40px] flex items-center justify-center")} style={{background: tagTypeColor[type][0]}}>
            {
                type === 'exchange' && <ExchangeIcon style={{width: 24, height: 24, color: tagTypeColor[type][1]}}/>
            }
            {
                type === 'normal_user' && <UserIcon style={{width: 24, height: 24, color: tagTypeColor[type][1]}}/>
            }
            {
                type === 'gamble' && <GambleIcon style={{width: 24, height: 24, color: tagTypeColor[type][1]}}/>
            }
            {
                type === 'scam' && <DangerIcon style={{width: 24, height: 24, color: tagTypeColor[type][1]}}/>
            }
        </div>
    )
}

const ProposalListItem = (props: proposal) => {
    return (
        <Link to='/vote'>
            <div className="flex flex-row gap-2 items-center">
                <ProposalIcon type={props.tag}/>
                <div className="flex flex-col flex-1">
                    <span>{props.tag}</span>
                    <span className="text-gray-400 text-sm">Eth Mainnet . {shortenAddr(props.address)}</span>
                </div>
            </div>
        </Link>
    )
}

export default ProposalListItem