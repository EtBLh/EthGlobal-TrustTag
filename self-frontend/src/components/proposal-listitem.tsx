import { proposal } from "@/lib/type"
import { shortenAddr } from "@/lib/utils"
import { Link } from "react-router"
import { ProposalIcon } from "./proposal-icon"

const ProposalListItem = (props: proposal) => {
    return (
        <Link to='/vote'>
            <div className="flex flex-row gap-2 items-center">
                <ProposalIcon type={props.tag}/>
                <div className="flex flex-col flex-1">
                    <span>{props.tag}</span>
                    <span className="text-gray-400 text-sm">Eth Mainnet · {shortenAddr(props.address)}</span>
                </div>
            </div>
        </Link>
    )
}

export default ProposalListItem