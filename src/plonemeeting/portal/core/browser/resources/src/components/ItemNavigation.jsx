const ItemNavigation = () => {
    return (
        <div id="querynextprev-navigation">
            <a id="query-nextprev-prev">
                <i className="bi bi-chevron-left"></i> Précédent
            </a>

            <span>
                1 sur 125
            </span>


            <a id="query-nextprev-next">
                Suivant
                <i className="bi bi-chevron-right"></i>
            </a>
        </div>
    )
}

export default ItemNavigation;
